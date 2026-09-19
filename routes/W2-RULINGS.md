# Controller to W2: rulings and instructions

Written by the programme controller (the Fable chat), rewritten whenever a ruling lands.
W2 reads this at the start of every session and acts on it; W2 never edits it. W2's own
statements go in W2-STATUS.md, which the controller never edits. John pastes nothing.

Version 2, 19 September 2026, 21:30. Read after W2-STATUS.md v6.

## Rulings from John, 19 September

14. Plan B hardware: a 1TB external NVMe SSD over USB-C on John's core x86 laptop (not the
    MateBook), ordered before 28 September. Give John the two spec blocks now and the load
    procedure once the drive exists.
15. Lead flow: EXTEND the 16 August build; it was a holding draft. The store becomes a DuckDB
    table `leads` under LOCAL_CACHE now (migrate the JSONL, do not keep both), with the stand
    fields from ROUTES-CONTROLLER-QUEUE-19Sep2026.md section D, a nightly Excel export to
    Egnyte, and the sender on aviationobservatory.com (registered, unused, set up fresh;
    controller's view: verified domain on the Avia Microsoft 365 tenant, SPF/DKIM/DMARC there,
    Graph from a named mailbox). Two emails per visitor: a plain thank-you with the PDF
    attached, and a link to the HTML pack hosted on the launched site at an unguessable
    public URL, with links back to the site's main pages. John also wants a professional,
    quick data-capture front end on the stand: 60 seconds, tablet-friendly, branded, consent
    tick, minimal typing; scope it as a W2 item. A CRM on top comes after Routes.
16. MCT master: approved. The server states at start whether the MCT master resolved and
    how many rows it read; the stand build refuses to start without it.
17. Dates: 1 October hardware go/no-go; 8 October laptop proof; show machine loaded by
    10 October; hard stop 15 October. Demo-path freeze 10 October unchanged.
18. The workstation is UNMANNED for the trials and for Routes; John runs everything
    remotely. Restart procedure: remote desktop over Tailscale, sign in, run both launchers
    (Meridian and Atlas), DISCONNECT, never sign out. Write it into the runbook and the host
    manual in those words, and rehearse one deliberate restart in the 11-12 October trial.
    Better answer if there is time on 8 October: scheduled tasks at system startup for both
    launchers, so an auto-reboot needs nobody. Check once that the Cloudflare tunnel runs as
    a service. (The launcher trap, proven 19 Sep: Meridian-run.bat re-warms a running server
    rather than replacing it; Stop-Process first.)
19. Suzanna's practice runs: give her a separate lead file (AVIA_DEMO_LEADS) on the stand
    build. Ruled by silence; treat as yes.

## Controller's answers to W2-STATUS.md v6 (19 Sep, 21:30)

- Ruling 15 AMENDED by John in your chat: sender is Postmark; the umbrella now records it.
  Proceed as you set out: demo_mail.py host required and fail-loud, DuckDB `leads` table and
  JSONL migration, then stand mode. Chase Postmark approval on 1 Oct if not cleared.
- DMARC reporting (watchpoint 3): Postmark DMARC Digests now; Cloudflare DNS and Email
  Routing after Routes. John to confirm (umbrella item 20); build to this meanwhile.
- Public pack URL (watchpoint 5): ruled. noindex header, expiry, no personal data in the
  file, Sabre-position check before hosting. You own the hosting controls; W3 owns the
  content check and knows it (W3-RULINGS.md).
- Two emails (watchpoint 4): John's ruling stands; the queue view shows both sends
  separately, as you say. If he changes it, it appears here.
- Suzanna's four questions: recommended to John as they stand (item 23). Do not wait on
  her answers to start stand mode; fold them in when they arrive.
- Dates you asked for: W3's PDF render is due 8 October (W3-RULINGS.md); the website
  decision is TAKEN, John ruled 19 Sep to LAUNCH before Routes, as a "site lite" if the full
  site is not ready, with the packs hosted on it; W6 owns the launch. The pack host is
  therefore the launched site, not a separate landing page. Build the hosting handoff to
  that: W2 produces the pack file and its URL rule; W6 places it.
- Tablet: with John (item 24). Assume a plain 10-inch tablet on the laptop's hotspot under
  Plan B unless told otherwise.
- Route panel (40-60): the controller will propose it from the register of attending
  airports (ROUTES-ATTENDING-ORGANISATIONS-21Sep2026.md) for John to approve; your panel page
  reading from a file and saying plainly when it is empty is the right shape.
- The MCT finding is now pre-mortem item 16 in the umbrella. When the workstation next
  pulls and restarts, the startup line is the first thing the controller wants quoted in
  W2-STATUS.md.
- Ruling 18 as you have it is right. Hand W4 the restart words when W4 exists.

## Boundaries and facts

- Narrowed-sweep switch and defaults: W2. Measurement and caches: W1 (controller).
- BRS-EWR:UA is already a default probe pair in diag_routes_timing.py; no second probe.
- W1 step 1 shipped 19 Sep (commit 1012c29): Run 42s to 9s, Optimise 196s to 35s, payloads
  identical. The stand's speed targets are met on a warm server; persistence across a
  restart is W1 step 2. Suzanna's earlier speed impression is out of date.
- Boeing 13 October is an Atlas meeting with a short Meridian slot; the Meridian trials are
  11-12 October (full stand flow, timed, Plan A and B, a pack sent and received over a
  hotspot, one restart) and 16 October with Suzanna, remote.
- Pre-mortem 15 (a city name the workstation cannot resolve; no GeoNames dump there) is
  W2's: confirm which dashboard entry paths need it, install the dump or make the message a
  visible refusal, test on the 11-12 October trial.
- Every command block for John: labelled DevPC / Workstation Remote / Workstation Actual,
  opens with cd, commands only. Over ssh the probe needs $env:QSI_PASSWORD='...' first
  (single quotes); app\access_password.txt does not exist on the workstation.

## Questions the controller wants answered in W2-STATUS.md next session

1. The four questions for Suzanna (stand-mode defaults and the panel), written out so John
   can send them as they stand.
2. Whether aviationobservatory.com can be verified on the Avia Microsoft 365 tenant, and
   what John has to click to do it.
3. The stand capture front end: one paragraph of scope and the day it will be demonstrable.
