# W3 status: presentation and pack

Written by W3 (Opus chat). Rewritten every session, never appended. The controller does not
edit this file; W3 does not edit W3-RULINGS.md. Session 1, 19 September 2026.

Read and confirmed this session: W3-RULINGS.md; GTM-STRATEGY-ROUTES-2026.md (Status block
read, not edited); ROUTES-COMMERCIAL-PLAN-19Sep2026.md sections 3, 5 and 10;
ROUTES-CONTROLLER-QUEUE-19Sep2026.md section B; PRICING-HANDOVER-19Sep2026.md;
ROUTES-ATTENDING-ORGANISATIONS-21Sep2026.md section 1; PROMPT-for-Fable-Routes-19Sep2026.txt;
HANDOVER-23Aug2026.md sections 5 to 7; MASTER-TASK-LIST.md.

Clone: DevPC `C:\AviaDev`, pulled by John 19 Sep. HEAD `7be1470` (this file, v1), pushed,
on `ad32627` (controller, W3 rulings v1). Workstation checked the same evening.
No git command run by W3 against the mount.

**Commit hashes landed this session:** `7be1470` (this file, v1). One commit owed, the
provenance fix in `deck/render_pptx.py`, block issued to John.

## State per scope item

| Item | State | Evidence | Next action |
|---|---|---|---|
| 1. Ten-slide stand deck | Not started, outline below | Only the 2 July `Avia_Cortex_Process_and_Methodology.pptx` exists, 6 slides, and it is not reusable as it stands (see Q1) | Build slides 1-6 and 9-10 on the outline; slides 7-8 wait on two live runs |
| 2. HTML pack tuned for the stand | Not started; the generator exists and three required sections do not | `app/pitch_html.py`, 399 lines, sections: opportunity, forecast, traffic table, market images, connecting markets, schedule and capacity, economics slider, why this route | Add the route map, the time-of-day curve and the tail chart; add a source line to every figure, not only the research cards |
| 3. PDF render | Not started, and now unblocked | Nothing in the repo renders a PDF (repo-wide search returns only `venv` noise). Workstation check PASSED 19 Sep, John's transcript: Chrome present at Program Files, `pikepdf` 10.10.0, `pillow` 12.3.0. Nothing to install | Build the print stylesheet and the render step on the next pull |
| 4. Imagery, provenance and airport photography | Provenance fix BUILT and PROVEN. Airport photography: scope widened by John 19 Sep, probe built, needs one workstation run | The library holds no airport photography for any of the six airports (Q3). The provenance loss is confirmed in code, and `piexif` 1.1.3 is present on the workstation (John's transcript, 19 Sep), so the EXIF fix runs where the decks are built | Commit the fix; run the coverage probe on the workstation; second source only if the measured gap justifies one |

## Built and proven this session: the provenance fix

`deck/render_pptx.py`, uncommitted in the working tree, block below. Three changes, none of
them on the engine run path and none in `cortex_app.py`.

1. `Assets._record` reads the rights record out of the source file, from PNG text chunks or
   from EXIF where the ingested file was already a JPEG.
2. `Assets._photo` writes that record into the JPEG as EXIF at save time. Where it cannot be
   written, the method keeps the source file rather than shipping a bare image, and reports
   the refusal. A photograph carrying no record at all is reported, never silently dropped.
3. `verify()` now reads the built file back and fails on any JPEG in `ppt/media` with no
   rights record, so the check runs on every build rather than on request.

Measured on `observatory_library/field/field-runway-sunrise.png`: 2,075 KB source to a 226 KB
JPEG, so the compression that exists for a sendable deck is unchanged, and the record survives
in full, author, copyright, the cleared line and the whole ingest record. An image with no
record is reported. Source: W3 run on the DevPC, 19 September.

**What the same check says about decks already sent.** `China Airlines TPE-SJC deck v2
19Aug2026.pptx` holds 224 media files, 94 of them JPEG, and **all 94 carry no rights record**.
Source: `_verify_provenance` run against that file, 19 September. Most of that imagery comes
from `C:\assets\engagement`, which holds no record to carry in the first place (Q3), so
re-rendering it will report rather than repair. Controller's call whether anything is owed on
decks already out; W3's scope starts at the Routes surfaces, where the check now blocks it.

## Airport photography: John's ruling of 19 September, and what W3 is doing about it

**Ruling (John, 19 Sep).** Mood frames and charts are essential and stay, but an airport sales
deck carries airport-specific photography. Draw on online sources, more than one, with paid
stock held for the airports a search cannot cover, so a photograph exists for most of the 300
plus airports in the room, in the deck and in the HTML pack. An airport uploading its own
library is the eventual answer and is a later build. **This widens W3-RULINGS scope item 4,
which reads "from the rights-managed Observatory library only". Controller to note.**

**The design point that decides the build, and it is already in the code.** `avia_images.auto_ok`
splits a confidential use from a published one. A photograph whose subject is a building, in a
country with no freedom-of-panorama exception, is ordinary practice in a pitch deck sent to a
named recipient and is refused on a public web page. John's 19 September ruling puts the HTML
pack on a public unguessable URL, which is a published use, while the emailed PDF is
confidential. So the same terminal photograph can be right in the PDF and wrong on the hosted
page, and the pack must resolve its images per use, not once per airport. This costs nothing:
`render_pptx.py` already takes `--use`, and the pack build must take it too.

**What already exists, and has never been run.** `deck/avia_images.py` does this job against
Wikimedia Commons and records the full licence block per file: ShareAlike files may be placed
but never cropped or graded, a country panorama table refreshed off Commons, no more than two
images from one photographer, a 1600 by 900 minimum, and non-free and fair-use templates
rejected outright. `C:\assets\engagement` holds **no `manifest.json`**, so the fetcher has
never written into it and every image in that folder was placed by hand. That is why the 94
JPEGs in the China Airlines deck carry nothing.

**W3's view: measure the coverage before signing up to anything.** Nobody knows what share of
400 airports Commons already covers at a usable size and licence, and that number decides
whether a second source is worth building and whether stock is worth buying. Signing contracts
first, then finding Commons covered most of it, wastes money and a fortnight W3 does not have
before the 10 October freeze.

**Built this session, ready to run:** `deck/build_image_set.py` generates the fetch-set input
from the engine's own airport table, ranked by size, joined to the airport reference for the
name and city each search needs. `deck/routes2026_probe.json` is the generated probe, 401
airports, one terminal slot each, including Genoa at 1.85m passengers precisely because a small
airport is the case worth measuring. It is committed generated, so the workstation installs
nothing to run it. The probe is a dry run: it searches and scores, downloads nothing.

The run must happen on the workstation. Commons is unreachable from the DevPC mount's shell,
which the egress proxy refuses with a 403, and `avia_images.py` says on its own first page that
it runs on the workstation and not in a sandbox. Block issued. It runs unattended while John is
away, alongside the preagg job.

**Sequence after the probe reports.** Where Commons covers an airport, that is the photograph
and it arrives with its record. Where it does not, W3 proposes one second source rather than
several, chosen on what its terms actually say when read, with Flickr's Creative Commons filter
the first candidate to read because aviation photography there is deep on named secondary
airports. Paid stock is a contract, not a build: W3 recommends signing nothing before Routes
and letting the measured gap decide it, because a gap airport still produces a good pack from
mood frames and charts, which is what the Observatory library was made for. The airport's own
uploaded library is the right long-term answer and already has its slot in
`avia_slots.SlotResolver(uploads_dir=...)`; it is a post-Routes build.

**The risk W3 will not trade away.** A photograph of the wrong airport, or one with no clearance,
handed to that airport's own route development team, is worse than no photograph. So the
pipeline refuses rather than guesses: no record, no placement, and the build check added this
session fails the deck rather than shipping it.

## Q1. The two methodology documents, and where they disagree

Paths, both in the project folder `C:\Users\Carte\OneDrive\Documents\Claude\Projects\Avia QSI Tool`:

- `Avia_Cortex_Process_and_Methodology.pptx`, 2 July 2026, 6 slides.
- `Meridian_Methodology_Note_Nick_23Aug2026.docx`, 23 August 2026, with
  `Meridian_Methodology_Process_Chart_23Aug2026.png` beside it. Marked private and confidential,
  internal only, because it carries Avia's own calibrated coefficients.

Master list 3.3b is now answered: they do contradict, in four places. W3 reports rather than
resolves.

1. **One engine or two.** The 2 July deck describes a single rebuilt engine producing the whole
   number in seven steps. Nick's note section 5 describes a second, calibrated method, a
   machine-learned launch model trained on real launches, running alongside the step-by-step
   build as a cross-check on the point-to-point figure. The deck does not mention it. The
   standing ruling in HANDOVER-23Aug2026.md section 7 reads "one engine, never a second engine".
   The ruling and the note use the word differently, and the accuracy claim belongs to the
   launch model, not to the step-by-step build. This is master list 2.4 and it reaches the stand:
   a visitor who asks what the 89% describes needs one answer. **Controller and John to settle
   the sentence; W3 will not write around it.**
2. **The accuracy figures themselves.** Nick's note gives accuracy in words ("the large
   majority", "a substantial share") and states that accuracy is reported separately for
   short-haul domestic and low-cost launches against long-haul international full-service,
   because a blended figure understates the harder segment. The ruled deck line is a single
   blended pair, 89 and 82. Nothing in the deck line is wrong, but the note invites the segment
   question the deck line does not answer. Nick has both documents.
3. **Two validation figures in the 2 July deck are pre-fix and must not be reused.** Slide 3
   claims the beyond feed reproduces the analyst's 48,115 to within circa 1% on BA London-San
   Jose, and that BA's beyond feed came out about 2.6 times a Star carrier's. Both predate the
   20 August each-way and two-way basis correction to the connecting layer. Either they are
   re-run on the current build and restated, or they stay out of the deck. W3 recommends they
   stay out: the deck has two live worked routes and does not need a July number.
4. **Naming and style.** The 2 July deck says "Avia Cortex" on every slide, which is a
   development name and never appears on a client surface, and it twice uses a word on John's
   banned list. No slide is reused as it stands; slides 2, 3 and 6 are useful as structure only.

Nick's note also carries a caveats list (section 6) that the stand must not contradict: weekly
frequency is not yet allocated to days, the local and connecting split is under review, and the
each-way or two-way basis must be stated. The deck states the basis on every passenger figure.

## Q2. The ten slides, one line each

1. Cover. Meridian, published by The Aviation Observatory. Route forecasting for airports and
   airlines. Stand F174, Routes World 2026.
2. The problem, in the buyer's words. A route development team pitches a route and is asked how
   many passengers, at what load factor, and why the airline should believe it.
3. What Meridian does. The seven-step build in the client's language, from two cities and an
   airline to annual passengers and the schedule to fly, restructured from 2 July slide 2.
4. The three classes of number: measured, calibrated, physics-capped, taken from Nick's note
   section 2. This is the slide the host uses to answer most method questions honestly.
5. The accuracy claim, alone on the slide, in the ruled words and nowhere else in the deck:
   calibrated leads are within 20% of the outcome 89% of the time and within 10% 82% of the
   time, on 2,915 real launches; blind results are reported as portfolios only, never as a
   single route.
6. The connecting feed, behind and beyond, and why the answer changes with the airline you
   pitch. Structure from 2 July slide 3, both July figures removed.
7. Worked route 1: SJC-TPE with China Airlines. Real charts from the tool, run on the current
   build, two-way basis stated, source line on every figure.
8. Worked route 2: one European transatlantic route, BLQ-JFK or GOA-JFK. Same layout as slide 7
   so the two read as one method, not two studies. **John picks the route and the carrier.**
9. The product family: Meridian, the Observatory Global Forecast, the Design Day module, and
   what each one answers. No competitor on this slide or any other.
10. The offer. The published structure only: 15,000, 20,000 or 25,000 pounds a year by airport
    size, three named seats, 100 generated presentations included, sales-led quotation, and
    "launch places this year on request". No discount figure, no number of places, no expiry
    until John rules (umbrella, Waiting on John, items 6 and 7).

Slides 7 and 8 need two runs on the frozen build to produce their charts. Everything else can
be built now. The four messaging sentences carry as placeholders from the controller queue
section B and swap on 25 September; they land on slides 2, 3 and 10.

## Q3. What the imagery library actually holds

Read at `C:\assets` on the DevPC (`ASSETS_DIR`), 19 September.

**The Observatory library holds no photography of any airport, including all six.** It holds 52
files in four families: globe (26 satellite frames by region), field (6 runway and approach
frames), operations (6 apron and tower frames), instruments (10 sextant, telescope and chart
still lifes). Every frame is cleared, "Observatory library, Collection 1 or 2, Avia Solutions,
2026-08-06", with the record in `library.json` and inside the file as PNG text. The library is
written as mood imagery, and its own note says so: "Mood only: covers, dividers, full-bleed,
closing pages. Never an evidence plate." One frame carries a restriction: a British Airways
livery is legible in `operations/operations-departures-gate.png`, usable only where BA is the
subject carrier and never auto-selected.

So the commercial plan's rule, hero image chosen by destination airport where the library has
one, resolves to nothing for SJC, TPE, BLQ, GOA, JFK and EWR.

There is a second folder, `C:\assets\engagement`, holding 39 files including San Jose aerials
and named corporate campuses from the SJC engagement. **It carries no rights record of any
kind, no manifest and no embedded record.** Nothing in it goes on a Routes surface under the
ruling, and W3 will not use it. `deck/avia_images.py` is the tool built to fetch named-airport
photography from Wikimedia Commons with the full licence record, and it has not been run for any
of the six. It must run on the workstation, not here, and its `fop-refresh` step runs first or
every country outside a twelve-country seed reads unknown, which blocks a published use.

**The provenance loss is confirmed, and it is in one place.** `deck/render_pptx.py`, method
`Assets._photo`, re-encodes photography to JPEG at quality 82 with `Image.open(path).convert
("RGB")` then `im.save(dest, "JPEG", ...)`, passing no EXIF. The library's record lives in PNG
text chunks, so it is dropped in that one call and every delivered deck carries images with no
rights record. Two ways out. The existing `--no-compress` flag keeps the PNGs and their records,
and the Liguria deck at 20MB is why the compression exists, so that is not the answer for an
emailed deck. The fix is eight lines: write the record into the JPEG as EXIF at save time with
`piexif`, exactly as `deck/avia_library.py::write_file_metadata` already does for JPEG inputs.
`piexif` 1.1.3 is confirmed present on the workstation, so the fix runs where the decks are built. W3 owns it and writes it on the next pull.

**What W3 needs from John on imagery.** With no cleared airport photography, there are three
options and W3 recommends the first. (a) The deck and the packs use Observatory mood frames for
covers and dividers, and the route slides carry charts and maps only, which is also what the
library's own rule says. Nothing is blocked and nothing is at risk. (b) Run `avia_images.py` on
the workstation for the six airports and take what Commons returns with its licence record,
which costs a workstation session and returns whatever depth Commons happens to have. (c) Buy
stock for the six. John's call.

## Q4. How the PDF render will be produced

Nothing exists, so this is a build from zero. Method, in W3's recommended order:

1. Chrome on the workstation in headless mode, driven by the existing Windows Chrome rather than
   a new dependency: `--headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf=<out>`
   against the pack's own URL on the local server, not a saved file, so the charts draw with
   their data and the fonts resolve.
2. A print stylesheet added to `app/pitch_html.py`: `@page { size: A4; margin: 14mm }`, page
   breaks held at the section boundaries so a chart never splits, the economics slider replaced
   in print by the figures at its current position, and the source line kept with its figure.
3. Metadata written after the render, because Chrome stamps its own: author and last-modified-by
   set to Avia Solutions with `pikepdf`, verified by reading the file back in the same script.
4. The render runs as a step in the pack job on the workstation, so the PDF and the hosted HTML
   come from one run and cannot differ. W2 owns what happens to the file after that.

**Nothing needs installing.** Checked on the workstation 19 September, John's pasted transcript:
Chrome present at `C:\Program Files\Google\Chrome\Application\chrome.exe`, `pikepdf` 10.10.0,
`pillow` 12.3.0, `piexif` 1.1.3. The Playwright fallback is not needed and is not added.

## What W3 needs from John

1. The pull on the DevPC and the HEAD hash, so W3 builds on the same tree (block below).
2. CLOSED 19 Sep: workstation checked, Chrome and `pikepdf` and `piexif` and `pillow` all present.
3. CLOSED 19 Sep: slide 8 is Bologna-New York. Carrier still to name.
4. CLOSED 19 Sep: mood frames and charts stay, and airport photography is added from
   multiple online sources with stock held for the gaps. Section above.
5. The coverage probe block, run on the workstation. It answers whether a second source and
   paid stock are needed at all, and nothing else should be bought until it reports.
6. The two July validation figures in Q1 item 3: W3 proposes they stay out. Silence to
   26 September, they stay out.

## For the controller

The one-engine-or-two wording (Q1 item 1) is a stand answer, not a document tidy, and it sits
with master list 2.4 and pre-mortem item 9. W3 needs the settled sentence before slides 4 and 5
are final, which is before 3 October.
