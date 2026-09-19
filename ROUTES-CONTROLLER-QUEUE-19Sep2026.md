# Routes programme: controller queue, drafted 19 September 2026

Written at the end of session 1 so the week of 22-27 September starts from this file, not from
scratch. John reads on a phone; every section fits a screen. Umbrella: GTM-STRATEGY-ROUTES-2026.md
(Status, Decisions log, Waiting on John). Nothing here is a figure; figures come from John.

## A. Where session 1 ended (19 Sep)

- HEAD DevPC 11a4c3f plus the probe commits; workstation pulled to the probe (07db0dd or later).
- Aircraft-econ code committed. Live check on the workstation owed: /api/aircraft lists 42 types
  (the probe prints it as its first row).
- Preagg build + identity chain running unattended on the workstation (E:\Avia\preagg_check\*.log).
  Read identity.log first on return: PASS means step D's wiring commit goes ahead; FAIL means
  read the differing columns before anything else.
- Timing probe: diag_routes_timing.py. Timings not yet taken. No optimisation proposals until
  they exist.

## B. Step C: the four messaging sentences (DRAFT for John and Jol; final by 25 Sep)

1. One-liner: "Run your route forecast on our stand, in seconds: 25 years of QSI practice, built
   into a tool and calibrated against real route launches."
2. Sub-messages (three, one clause each): "The best time of day to fly it, not just how many
   will fly it. A researched pack with your numbers in your inbox within 30 minutes. Independent
   and senior: no network to sell you, no house view."
3. The offer (structure only; numbers from the pricing chat): "Expected list price around [X]
   a year, stated as a soft figure; [N] launch places this year at [Y]% off year one, in
   writing, expiring [date]."
4. Accuracy, exactly as ruled: "Calibrated leads are within 20% of the outcome 89% of the time
   and within 10% 82% of the time, on 2,915 real launches; blind results are reported as
   portfolios, never as a single route."

Rules applied: no competitor; no "illustrative"; no feature not in the frozen build.

## C. Step C: decisions John owes this week (answer by number; silence has a stated result)

1. Pricing numbers for sentence 3 (X, N, Y, expiry) from the pricing chat. Silence to 3 Oct:
   sentence 3 leaves the messaging and the host says "on request, limited places" only.
2. Meeting targets: five from the candidate pools (commercial plan 9). Silence to 26 Sep: no
   invitations go, and the meetings are whoever walks up.
3. Email sender for the pack: Microsoft Graph from the Avia tenant (my view: it is already
   reachable, SPF/DKIM already right for aviasolutions.com, no new supplier) or Resend/Postmark.
   Silence to 26 Sep: I build against Graph.
4. Lead store: workstation DuckDB (my view: one table the form writes, exported nightly to
   Egnyte as Excel, readable on a phone via the export; no new supplier before launch) or a
   CRM. Silence to 26 Sep: DuckDB.
5. Attending-airport list source for pre-warm: the Routes delegate list as it is published, or
   the exhibitor list now. Silence to 1 Oct: exhibitor list now, delegate list added when out.
6. Stand host: name, contact, start date; stand number. No default possible.
7. Website: launch or landing page, by 1 Oct (Jol's pace decides). Silence: landing page.

## D. Step E: request queue and email, on one screen (stop for John's answer before building)

- Store: DuckDB table `leads` under LOCAL_CACHE (name, company, role, email, phone, route,
  airline, pitching_at_routes, buyer, consent, interest, pack_sent_at, pack_error, follow_up
  owner/date, notes, run signature of the exact run shown). Written by the stand form; cards
  typed in at end of day; nightly export to Egnyte as Excel via the existing refresh pattern.
- Queue: reuse /api/pitch/start + job_watch; a `queue` view page (running / sent / failed,
  newest first, failure reason visible) in stand mode.
- Sender: decision 3. From a named person (John), reply-to John, subject "Your <ORIG>-<DEST>
  forecast from the Meridian stand at Routes".
- Email wording (draft): "Thank you for running <ORIG>-<DEST> with us on the stand today.
  Attached is the pack with the numbers you saw, and the workbook behind them. Does it match
  what you have run? A reply with the gap is the most useful thing you can send us. [Host] and
  I are on the stand until Thursday; a follow-up call is booked/offered for [slot]." Signature
  John. Nothing linking to a login.
- Pack contents: the HTML pitch, the workbook, the PDF render (build item), cover note. Every
  figure with its source line; accuracy wording as ruled; economics disclaimer present.
- Consent: tick on the form, privacy line on the card; store on Avia infrastructure only.

## E. Workstream briefs, one paragraph each, for a dedicated chat if John spawns one

Each sub-chat reads the umbrella's Status first and reports back into it; it never edits the
Status block itself. Standing rules of the prompt apply verbatim.

- W1 Speed (after timings and identity PASS): wire preagg into the live path (feed_cfg and
  backtest._PREAGG from a config path AVIA_PREAGG, no silent fallback: log ON/OFF at start);
  persistent result cache keyed on the full run signature plus store vintage, component-level
  and run-level, under LOCAL_CACHE; pre-warm by airport script; narrowed default sweep behind
  a stand-mode switch; raise DuckDB caps for the workstation and measure. Probe before/after.
- W2 Stand flow: stand mode switch; request form; queue view; progressive Optimise display
  (departure curve first, sweep rows as they finish); laptop build (config BUILD=laptop)
  proven cold on a laptop by 1 Oct or declared dead; Plan A/B rehearsal script.
- W3 Presentation: 10-slide deck rebuilt from Avia_Cortex_Process_and_Methodology.pptx (2 July)
  after checking it against Nick's methodology note (master list 3.3b); HTML pack tuned; PDF
  render via headless Chrome; imagery from the rights library with provenance intact (fix the
  PNG-to-JPEG strip); Observatory palette; Avia author; en-GB.
- W4 Host: STAND-HOST-MANUAL.md per commercial plan section 4; timed script on two routes;
  objections page; Plan B page; queue view page; "what not to say".
- W5 Leads and order-ready: section D above; the order-ready checklist (umbrella 3) tracked
  item by item from 24 Oct.
- W6 Messaging and marketing: sentences in B; posts and emails drafted weekly for approval,
  never posted; exhibitor listing text; website path per decision 7.
- W7 Rehearsal: freeze 10 Oct; Boeing 13 Oct runs the Routes flow exactly, timed, on hotel
  wifi; fix list from Boeing; Plan B kit go/no-go.

## F. First actions next session, in order

1. Read E:\Avia\preagg_check\identity.log (tail 20) and build.log; record in Status.
2. Read TIMING-*.md if John ran the probe; otherwise run it over ssh on two never-run pairs.
3. Take John's numbered answers to section C into the Decisions log; anything silent takes the
   stated default and is logged as such.
4. Then, and only then, W1 proposals from the measured numbers.
