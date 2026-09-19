# Controller to W4: rulings and instructions

Written by the programme controller (the Fable chat), rewritten whenever a ruling lands.
W4 reads this at the start of every session and acts on it; W4 never edits it. W4's own
statements go in W4-STATUS.md, which the controller never edits. John pastes nothing.
Read routes/README.md first: it says who writes which file, who owns which code, and how conflicts are reported and resolved.

Version 2, 19 September 2026, 23:30. Read after W4-STATUS.md v1.

## Scope (commercial plan section 4; umbrella W4)

One document, C:\AviaDev\routes\STAND-HOST-MANUAL.md, then a printed copy (Word, A4, Avia
Solutions as author, en-GB, later). Contents, in this order:

1. Who we are, in 90 seconds: Avia independent since 2001, senior operators not a bench;
   Meridian, published by The Aviation Observatory, 25 years of QSI practice made into a
   tool and calibrated against real launches.
2. The three classes of number: measured, calibrated, physics-capped (Nick's note, section 2,
   at C:\Users\Carte\OneDrive\Documents\Claude\Projects\Avia QSI Tool\
   Meridian_Methodology_Note_Nick_23Aug2026.docx, internal, coefficients never quoted).
   If the host cannot answer a method question: "John can take you through the method in
   detail, shall I set that up".
3. The demo script, timed: opening line; Run on the visitor's route and what to point at as it
   lands (market background, capture, the time-of-day curve); Optimise for the interested and
   what to say while it fills; the pack explained with two pre-built examples; the capture
   form; the close. Two rehearsed routes for walk-ups with no route in mind.
4. What not to say: no feature not in the frozen build (day-of-week allocation, fare in the
   QSI score and the new aircraft types' economics are post-Routes); no price beyond "launch
   places this year on request"; no single-route blind accuracy figure; no comparison with
   any competitor; if a visitor names one, the one honest sentence (commercial plan 10) and
   listen.
5. Plan B, step by step, with phone numbers: what to do when the network drops, in what
   order, and the restart words for the workstation.
6. The queue view: how to see a pack was sent, what to do when one fails.
7. Objections and answers, one page: "we have our own model"; "how accurate is it really";
   "where does the data come from"; "can it do day-of-week or fares" (honest: on the
   roadmap); "what does it cost"; "the forecast is wrong, we know our market" (this is the
   product working: "a gap is informative; which side do you think is right, and why";
   capture the reason; never defend a number on the stand).
8. The day: setup, breaks, who is on the stand when, the end-of-day lead review with John,
   the five feedback questions after each substantive demo (commercial plan 6.2).

## Facts and rulings you build to

- Host: Suzanna McIntosh, a former OAG demo lead, has used Meridian for about four weeks and
  has Cloudflare Access. Lands Tuesday 20 October afternoon; works the stand Wednesday to
  Friday 9 to 5. Stefan Parry (summer intern, also a user) may join her. Stand F174,
  Frankfurt. Training is REMOTE: two video sessions on the frozen build between 14 and 16
  October, and a full run-through on 16 October with Jol playing a sceptical airport; John
  is not in the country for an in-person session.
- Accuracy wording, verbatim and only this, everywhere in the manual: calibrated leads are
  within 20% of the outcome 89% of the time and within 10% 82% of the time, on 2,915 real
  launches; blind results are reported as portfolios only, never as a single route. The
  one-sentence explanation of what that describes is OPEN with John (umbrella item 25);
  leave a marked slot for it and do not invent one.
- Price, if asked: the published structure only, £15,000, £20,000 or £25,000 a year by
  airport size, three seats, 100 presentations included, and "launch places this year on
  request". No discount figure, places or expiry until John rules.
- The restart words, verbatim, from W2: remote desktop over Tailscale, sign in, run both
  launchers (Meridian and Atlas), DISCONNECT, never sign out; Stop-Process first because
  the launcher re-warms a running server rather than replacing it. The host does not do
  this; she rings John, and the manual says who else to ring if John cannot be reached.
- Stand mode (W2): the host works in stand mode; Expert mode stays visible in the nav as
  evidence of depth and she may point at it but does not open it. The capture form is one
  screen on a tablet, 60 seconds, route and airline pre-filled from the run just shown;
  consent tick; everything past email optional. Two emails follow each capture: a
  thank-you with the PDF, and a link to the hosted HTML pack.
- The two pre-built pack examples and the two rehearsed walk-up routes: SJC-TPE (China
  Airlines) and Bologna-New York; the same two as the deck's worked routes (W3), so the
  host tells one story.
- The pre-mortem in GTM-STRATEGY-ROUTES-2026.md section 6 is the manual's checklist: every
  item that names the host must have its answer in the manual, in her words.
- Nothing about any competitor anywhere in the manual beyond section 4's sentence. The
  organisations file's section 8 (who uses the direct competitor) is for John's briefing
  of Suzanna by voice, not for the printed manual.
- Voice note-taking on the stand is under consideration (John); if it is used, the manual
  carries the consent line the host says before recording.

## Dependencies you do not wait for

- W2's stand mode, capture form and queue view are being built; write those sections to the
  design above and mark the screenshots to be added after 8 October.
- W3's deck and pack examples land 3 and 8 October; reference them by name.
- The accuracy sentence (item 25) lands by 26 September; the slot is marked.

## What the controller wants in W4-STATUS.md after session 1
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

- W4 specifics: your three conflicts are resolved above (the pack promise as you proposed;
  pricing per item 29; W5's feedback wording). Section 6.5's slot reads "follows the same
  day". Your three questions to John are umbrella item 34. The rehearsed routes change if
  item 28 changes the deck's; track W3-STATUS as you do. Manual v1 is read and is good.


1. The manual's skeleton with sections 1, 2, 4, 7 and 8 drafted in full and 3, 5, 6 drafted to
   the design with marked gaps.
2. The timed demo script for one route, to the second, so John can read it against a real Run.
3. The three questions the manual cannot answer without John, if any.
