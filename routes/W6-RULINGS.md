# Controller to W6: rulings and instructions

Written by the programme controller (the Fable chat), rewritten whenever a ruling lands.
W6 reads this at the start of every session and acts on it; W6 never edits it. W6's own
statements go in W6-STATUS.md, which the controller never edits. John pastes nothing.
Read routes/README.md first: it says who writes which file, who owns which code, and how conflicts are reported and resolved.

Version 2, 19 September 2026, 23:30. Read after W6-STATUS.md v3; scope item 4 rewritten.

## Scope (commercial plan sections 7, 8 and 9; umbrella section 4 and W6)

1. MESSAGING. The four sentences (one-liner; three sub-messages; the offer; the accuracy
   line), drafted in ROUTES-CONTROLLER-QUEUE-19Sep2026.md section B. W6 refines them into
   two or three variants each for John and Jol to choose from by 23 September; John settles
   them by 25 September. The accuracy line is not a variant: it is verbatim and fixed.
2. INVITATIONS to the five pre-arranged meetings, drafted in John's voice, one paragraph
   each, for John to send 26-29 September through the Routes meeting system or email. The
   five are John's pick from ROUTES-ATTENDING-ORGANISATIONS-21Sep2026.md section 3 (he has
   agreed the buyer-test list: Birmingham, Dublin, Vienna, Dallas Fort Worth, Milan SEA;
   reserves there). Each invitation names the route Avia will pre-run for them; W6 proposes
   the route per airport from public pitching activity, stated as a proposal.
3. MARKETING CALENDAR, drafted for approval, never posted by you: week of 22 Sep, John's
   LinkedIn post announcing the stand and "run your route live", with one real chart (the
   SJC-TPE time-of-day curve, from the tool, source line on it), and an email to the client
   and contact list ("book ten minutes on the stand"); week of 29 Sep, the Routes exhibitor
   listing and app profile text, and post 2 (the three classes of number in plain words);
   week of 6 Oct, post 3 (a worked route, the pack as a PDF image); week of 13 Oct, the
   final "see us at F174" note; during the show, one post a day from the stand with the
   visitor's permission and no numbers that identify their pitch. Every piece goes to Jol
   for copy and to John for approval; nothing is published by a chat.
4. WEBSITE, REWRITTEN after John's rulings in your chat. The site to launch is THE AVIATION
   OBSERVATORY site (repository at E:\Avia\Observatory Website, 22 pages, Eleventy; naming
   register: `tao-website`), on aviationobservatory.com, deployed by Avia on Cloudflare Pages
   from the repository, not from the workstation; the IT firm is not on this path. Order of
   work: (1) the repository gets a GitHub remote and is pushed THIS WEEK (John runs your
   block; tool standard 1; until then 22 pages sit in one folder); (2) the competitor comes
   out of the header, footer and every page (eight files) and the prices come out of the
   seven files that carry them, held until November (umbrella item 29); (3) the ruled
   accuracy line goes on the Meridian page, verbatim; (4) a clean-clone build proves the
   Eleventy config; (5) Cloudflare Pages deployment on the zone W2 moves in the week of 22
   Sep, with a preview branch so nothing publishes by accident; (6) the packs are hosted on
   the workstation tunnel at a pack hostname (W2 mechanics, by 8 Oct), linked from the site.
   W6 edits the repository directly through blocks John runs (silence to 23 Sep: yes). A
   review branch and preview before any editor is pointed at the live site; the editor moves
   to this site after Routes.
5. MEETINGS LOGISTICS: each of the five meetings has its route pre-run, the pack printed,
   Optimise live, and the one-pager left behind; W6 keeps the schedule and the pack list.

## Rulings and facts you build to

- Nothing about any competitor in any material, post, page or email. The staging site
  carries a competitor comparison page: it is WITHHELD from the launch (umbrella item 11
  awaits John's confirmation; build the plan on withholding it).
- Pricing on the site: the published grid (£15,000 / £20,000 / £25,000 a year by airport
  size, three seats, 100 presentations included, sales-led) goes live only with John's
  sign-off, per PRICING-HANDOVER-19Sep2026.md section 3 item 5; the "provisional, not for
  publication" banner comes off only then. No discount, places or expiry anywhere until
  John rules (umbrella item 6).
- The accuracy line, verbatim and only this: calibrated leads are within 20% of the
  outcome 89% of the time and within 10% 82% of the time, on 2,915 real launches; blind
  results are reported as portfolios only, never as a single route. No single-route blind
  figure on any surface. The one-sentence explanation of what it describes is open
  (umbrella item 25); until it lands, no copy elaborates on it.
- Product naming on every client surface: Meridian, published by The Aviation Observatory.
  Avia Cortex never appears. Avia Solutions is the consultancy; The Aviation Observatory
  publishes the products.
- Chart on the first post: from the tool, on the current build, unit and period and
  "forecast" stated on the image, source line on it. No chart from research or memory. The
  ROUTE is with John (umbrella item 28); your BRS-EWR proposal is the controller's candidate
  too. Silence to 23 Sep: BRS-EWR.
- The invitations and posts are drafts in John's voice; he edits and sends. The email to
  the contact list goes from John's Avia address; the pack emails go from
  aviationobservatory.com (W2's domain, Postmark).
- Voice for copy: Avia house style, UK English, no em or en dashes, active voice, no
  consultant-generic words; short sentences on LinkedIn; "circa" not "approximately".
- Frankfurt, 21-23 October, stand F174. Suzanna McIntosh hosts.

## Dependencies

- Jol: copy on everything; the site rewrite. W6 writes what Jol must finish, by page, with
  a date, and John carries it to Jol.
- The IT firm: the cutover. W6 writes the request in one paragraph for John to send.
- W2: pack files and URL rule (for hosting); the sender domain.
- W3: the SJC-TPE curve image for post 1 and the pack PDF image for post 3.
- The Observatory site repository is separate from the Meridian repo; C:\src\avia-website
  (the editor) is requested from John as a folder grant (umbrella item 32).


## Sweep of 19 September, 23:30: rulings that reach every workstream

- THE PACK PROMISE: every outgoing word says the pack "follows the same day" until the sender
  is out of test mode and one pack has been sent and received over a hotspot at the 11-12
  October trial. "Within 30 minutes" only after that. Ruled by the controller.
- WORKED ROUTES: John's standing rule for demo and marketing material is never to use an
  airport Avia has worked for. The deck's routes, the host's rehearsed routes and the post-1
  chart all currently do. Umbrella item 28 asks John to rule by 23 Sep; candidate pair
  BRS-EWR plus a US origin. Do not build anything route-specific that is expensive to redo
  until it lands; everything else proceeds.
- PRICING, one position (umbrella item 29, proposed, silence to 26 Sep means yes): host says
  the expected list range by airport size and "launch places this year on request" only if
  asked; the one-pager and the deck's last slide carry the grid in writing; the website does
  not publish prices until November.
- TIER SHAPE: the published grid; airlines and advisers "quoted".
- FEEDBACK QUESTIONS: W5's card wording is the only wording; W4's manual and any W2 screen
  quote it with its version.
- DNS: aviationobservatory.com moves to Cloudflare in the week of 22 Sep (W2); Email Routing
  gives the domain an inbound address; W6's site deploys on Cloudflare Pages from the same
  zone; Postmark records re-verified after the move.

- W6 specifics: your five conflicts are resolved above and in the umbrella (scope 4 rewritten;
  IT firm off the path; pricing per item 29, which adopts your recommendation for the site;
  chart per item 28; decision 7 recorded as answered with W2 owning the pack hostname). Your
  status v3 is read. Post 1 and the list email wait on item 28's route only.

## What the controller wants in W6-STATUS.md after session 2

1. The repository push confirmed with the remote's URL and HEAD.
2. The competitor and price removals as a file list, built on a clean clone.
3. Invitations updated to "follows the same day" and to item 28's routes when ruled.

## What the controller wanted after session 1 (delivered)

1. The four sentences in two or three variants each, ready for John and Jol.
2. Five invitation drafts with the proposed pre-run route for each.
3. Post 1 and the contact-list email, drafted.
4. The site launch plan: pages, owners, dates, the two takedowns, the IT firm's paragraph.
