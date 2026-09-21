# W3 status: presentation, pack and stand video

Written by W3 (Opus chat). Rewritten every session, never appended. The controller does not
edit this file; W3 does not edit W3-RULINGS.md. Session 2, 21 September 2026.

Read this session: routes/README.md; W3-RULINGS.md v3 in full, including the pricing pointer,
the sweep of 19 September and scope item 5; routes/PRICING-DECISION-2026.md v1.0 FINAL,
sections 7, 10 and 11; the umbrella's items 25, 26, 28 and 45.

Clone: DevPC `C:\AviaDev`. W3 runs no git against the mount; John runs every block.

**Commit hashes landed.** `7be1470` status v1 - `45a5210` the provenance fix in
`deck/render_pptx.py` - `86999cc` the fetch-set builder and the probe (this one wears
`45a5210`'s subject line; W3's error, recorded here because the history is not rewritten for a
subject line) - `02ed18d` three airport images per airport - `f1fa7e3` the byte-order-mark fix
- `83d547b` the development name off every client-facing surface - `03030fc` and `aa1c25b`
status - `3af5158` the ten-slide stand deck.

**Owed from this session, two commits, blocks issued:** the deck corrected to final pricing,
and the PDF render with its print stylesheet.

## State per scope item

| Item | State | Evidence | Next action |
|---|---|---|---|
| 1. Ten-slide stand deck | Slides 1-6 and 9-10 BUILT and verified; 7-8 held | `deck/spec_routes_stand.py` at `3af5158`, corrected this session to PRICING-DECISION-2026.md v1.0. Renders clean: author and last-modified-by The Aviation Observatory, en-GB the only language on every run, no em or en dashes, rights record on the cover photograph. `Meridian_Routes_Stand_Deck_DRAFT_v0.2.pptx` in John's QSI Tool folder | Swap the messaging sentences on 25 Sep; slides 7-8 from runs 29 Sep-1 Oct |
| 2. The pitch page (HTML) | NOT STARTED. Next build | The existing pack is a scrolling document; John ruled on 19 Sep that the HTML is a page presentable in a 20-minute airline meeting, and the PDF carries the depth | Rebuild as slide-shaped sections. The three figures are NOT new work: they exist and two are live (see below) |
| 3. PDF render | BUILT and PROVEN | `deck/pack_pdf.py` plus a print block in `app/pitch_html.py`. Two-page A4 PDF, 56.6 KB, 1.2 seconds, every page 595 x 842 points, author and producer Avia Solutions | Render one real pack on the workstation, where the server and the stores are |
| 4. Imagery | Provenance fix BUILT and PROVEN; coverage UNKNOWN | The fix is live and the deck build proves it end to end: a 2,075 KB library PNG became a 211 KB JPEG still carrying author, copyright and the cleared line. `deck/routes2026_probe.json`, 401 airports, three airport slots each | **The probe run. Blocked on one workstation paste since 19 September.** Block re-issued |
| 5. Stand video (NEW) | NOT STARTED | Brought under W3 by John, 21 September. Scenarios agreed 9 September | Script and shot list next, then record on the Dev PC |

## Scope item 5: the stand video, and its dates

A silent, subtitled loop for the stand TV in the Observatory look. Three cuts: the 3-4 minute
booth loop, a 90-second insurer cut, a 20-30 second GIF for W6's posts.

- Routes: Bordeaux (easyJet or Vueling, short haul) and Boise (Breeze or Southwest). **A third,
  larger hub for a long-haul pitch is with John, umbrella item 45.** Never a client airport,
  which is John's standing rule for demo and marketing material.
- Each route: warmed off camera, one run shown live with a time-lapse caption. The accuracy line
  verbatim once and nowhere else. "About a minute" is released (W6-RULINGS, 21 Sep) and may be
  captioned for Run only. Nothing about any competitor; nothing labelled illustrative.
- Recording: natively on the Dev PC with a labelled block, because the portal at
  meridian.aviacortex.com is not reachable from this chat's environment. Post-processing in the
  device shell with ffmpeg. The password file is never printed.
- Delivery: the booth loop as MP4 in 16:9 for the stand TV, with W9 confirming the screen's
  input and resolution from the exhibitor manual; the GIF to W6.

| Date | Video milestone |
|---|---|
| 23 Sep | Script and shot list to the controller; John names the third route (item 45) |
| 26-30 Sep | Record the two agreed routes on the Dev PC; rough cut |
| 3 Oct | **First cut to Jol and Nick, with the other four items** |
| After 10 Oct | Final cut re-recorded on the frozen build |
| 15 Oct | On the show laptop and a USB stick; W2 loads it |

The third route is the only hard dependency. Without it by 23 September the first cut carries
two routes rather than three, and W3 says so rather than substituting one.

## What changed in the deck this session

The pricing ruling landed after the deck was built, so slide 10 was wrong within a day of
being right.

- Slide 10 rebuilt to **one pricing line quoting PRICING-DECISION-2026.md v1.0, nothing more**,
  in the ruled host wording of section 7. The size bands are gone, because the axis is airports
  covered and not airport size. No number of places, because John ruled there is no limit. The
  order-ready line is added: the agreement and onboarding are available immediately after Routes.
- **No airline price appears anywhere.** The old slide carried "airlines, consultancies and
  multi-airport groups are quoted on their portfolio"; Avia's Sabre licence does not permit
  selling to airlines, so no airline is sold, quoted or priced on any W3 surface (decision 20).
- The pack promise is now "emailed the same day" and no minutes figure, per the controller's
  ruling of 19 September carried into the pricing file's section 7. The placeholder sentence
  from the controller queue says thirty minutes; the ruling beats the placeholder.
- Slide 9 loses the Design Day pricing wording, which came from the superseded handover.
- Stand F174 corrected to F124.

## Correction: the pitch page's three figures already exist (John, 21 September)

John asked W3 to check the SJC-TPE work before reinventing it. He was right to, and W3's own
line in the session-1 status, that the route map, the time-of-day curve and the tail chart "do
not exist in the pack at all", was true of the pack and wrong about the codebase. The
difference is days of work.

- **Time-of-day curve: BUILT, WIRED, LIVE.** `app/cortex_workbook.render_curve_png()`, built
  24 August for John's EVA, China Airlines and STARLUX batch. Matplotlib rather than openpyxl's
  native chart, because the shaded restricted-hour bands and the annotated callout cannot be
  done in the Excel chart model without hand-editing chart XML. It is rendered before
  `wb.save()` and embedded in the Departure curve sheet, with the raw data table and a native
  Excel line chart beside it. Its comment carries the lesson: it rendered correctly to a
  sibling file on the server for a while, and three real bug fixes achieved nothing until it
  travelled inside the file John actually clicks.
- **Route and catchment maps: BUILT and WIRED.** `deck/forecast_pack.render_maps()` through
  `deck/avia_maps.route_map()`, both route ends, reached from `app/demo_pack.py`. A pack that
  cannot draw a map is still a pack, by design.
- **Tail chart: BUILT.** `drawTail()` and `tailPattern()` in `app/cortex_dashboard.html`, with
  the day-of-week seam marked. JavaScript, which is what the pitch page is, so it lifts across.
- **The workbook is eight sheets**, not a spreadsheet: Forecast, Connecting feed, Schedule,
  Departure curve, Catchment, Economics, Competition, Assumptions, each with each-way and
  two-way pairs, a method note, source lines, and Avia Solutions set as creator and
  last-modified-by.

**What this changes.** The pitch page is selection and wiring, not invention. The eight sheets
are the content inventory already argued out, so the question is which of them earn a place in
twenty minutes, not what the figures should be.

**One judgement W3 will make unless the controller rules otherwise.** John's 19 September
ruling asks for interactive charts on the pitch page. The curve is a proven, labelled,
source-lined PNG whose numbers match the workbook. Building a second, interactive curve risks
two pictures of the same run disagreeing, against the download-fidelity ruling that a download
reproduces the run on screen. So W3 uses the proven renderers where a figure carries numbers,
and adds interactivity only where it earns its place: the economics sliders, which already
exist and already work.

## Conflicts seen (README: W3 reports, the controller resolves)

1. **The deck's author.** W3-RULINGS scope item 1 says Avia Solutions as author and
   last-modified-by. The naming ruling and `render_pptx._metadata`'s own documented rule say a
   product deck is published by The Aviation Observatory, and every slide is branded that way.
   Built as the Observatory. One line to change.
2. **The accuracy wording.** The ruled line is binding verbatim; umbrella item 25(b) states the
   same figures in different words. Both on slide 5 would breach "no other accuracy figure
   anywhere", so the ruled line is on the slide and 25(b) is in the speaker notes. The
   controller rules which is the slide text when item 25 lands.
3. **Dates inside the rulings file.** The Dates line still reads "pack tuning and PDF render by
   8 October; imagery rights fix by 8 October", while the sweep below it records and accepts
   John's 3 October for all items. W3 works to 3 October.
4. **Slides 7 and 8.** Scope item 1 puts two worked routes with real charts in the deck due
   3 October, while the controller's answer takes those runs only after the 10 October freeze.
   W3's proposal, unchanged: the layout and the argument go to Jol and Nick on 3 October with
   charts from the current build, and the charts are regenerated off the frozen build between
   10 and 14 October before anything is printed. Reviewers are judging the slide, not the third
   decimal place.

## What W3 needs

1. **The coverage probe, on the workstation.** Blocked since 19 September, twice on this
   chat's own faults, both fixed. Block re-issued. If it has not run by 26 September W3 stops
   planning for airport photography and the Routes surfaces carry Observatory mood frames and
   charts, which is a decision rather than a discovery.
2. **The carrier for Bologna-New York** (umbrella item 26). Named on slide 8 and an input to
   the run.
3. **The third video route** (umbrella item 45), by 23 September.
4. **The accuracy sentence** (umbrella item 25), by 26 September. Slides 4 and 5 are built to
   hold the fallback wording and swap.
5. **Two runs off the build** for the worked routes, 29 September to 1 October.

## For the controller

- Scope item 5 lands on the same 3 October as the other four, and it is a recording job on the
  Dev PC rather than a build in this chat. It is the item most likely to slip, because it needs
  the portal, a screen recorder and a quiet machine, and none of that can be proven from here.
- The pack promise change reached the deck this session. If any other W3 surface is quoted
  elsewhere with a minutes figure, it is out of date.
- Item 28 closed on SJC-TPE and Bologna-New York for the deck. The video keeps the
  never-a-client-airport rule separately, which is right: the deck's job is evidence and the
  video's job is demonstration.
