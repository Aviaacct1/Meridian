# W4 host: status

Written by the W4 chat for the programme controller. Rewritten every session, never appended.
W4 does not edit W4-RULINGS.md, the umbrella or any other workstream's file. Version 2,
21 September 2026, session 2.

## Live state

`STAND-HOST-MANUAL.md` v2 written, 862 lines, 23 marked slots, no invented fact. Sections 1 to 8
all drafted; 3, 5 and 6 still carry W2's build gaps and the screenshots. Slots for umbrella items
25 and 34 kept open as John instructed.

Read this session: `routes\README.md` v1; `W4-RULINGS.md` in full as at 21 September, including
the pricing pointer, the 19 September sweep, the 20 September order-ready ruling, Suzanna's four
answers of 20 September 21:45, John's accuracy-conversation ruling of 20 September 22:15 and the
item 28 closure; `PRICING-DECISION-2026.md` v1.0 sections 7, 10 and 11, with 2, 3 and 4 for the
licence shape; `W2-RULINGS.md` the recorder ruling of 21 September; `W2-STATUS.md` v13;
`W3-STATUS.md` v1; `W5-FEEDBACK-CARD-19Sep2026.md` v0.1; `GTM-STRATEGY-ROUTES-2026.md` Status,
items 6, 25, 26, 34 and the pre-mortem. Also read `app/methodology_page.py` on the DevPC clone
for the bridge chart's real step labels, which section 7.6 now quotes.

No git command run by W4 against the mount. HEAD not confirmed this session: the pull block is at
the foot of this file and the tree already carries the 20 and 21 September rulings, so v2 is
built on what the clone holds rather than on a confirmed hash. John's paste closes that.

## What changed in the manual, and what ruled it

| Manual | Change | Ruling |
|---|---|---|
| Header | v2, with a summary of what moved, for a reader who knows v1 | |
| 3 | Entry order is hers: origin and destination, then left to right, blanks optimise; one line separating Run Assessment from Optimise, with a slot to match W2's screen words | Suzanna's answers 1 and 2, 20 Sep |
| 3, 3.3 | The demonstration finishes on the forecast; the pack shown is pre-made on a rehearsed route; the visitor's own arrives by email the same day | John's stand flow, 20 Sep, quoted in pricing 7 |
| 3.3a NEW | The five weak scenarios to steer round, with a slot for W5's list of 1 Oct to replace them | Suzanna's answer 3a; controller ruling |
| 3.4 | "Is route development done here, or at group?" is now the first qualification question, with why a group delegation may be the buyer | Pricing 7 and 10 |
| 4.2 | Rewritten: one sentence, nothing further unprompted | Pricing 7 |
| 4.6 NEW | Meridian is not sold, quoted or priced to an airline, with the words for a network planner who asks | Pricing pointer in W4-RULINGS |
| 6.5 | The pack follows the same day. No minutes figure anywhere in the manual | Controller sweep 19 Sep; pricing 7 |
| 7.5 | Rewritten to the ruled sentence verbatim, with the qualifying question first, the five things she may add if pressed, the six she never says, and the new signing answer | Pricing 7; order-ready 21 Oct ruling |
| 7.6 | Rewritten as the bridge walk-through: forecast against forecast, the eight steps in her words, "which step do you think is different, and why", John's two cases | John, 20 Sep 22:15 |
| 7.11 | Rewritten: the whole product, no user count, no metering, fair use as a clause and never a counter | Pricing 2 and 3 |
| 8.5 | The two spend questions added, with a slot for W5 to carry them on the card | Pricing 7, decision 13 |
| 8.6 NEW | The recording: never covert, the notice and the spoken line as drafts awaiting W2, voice note and card drop primary, the recording a backstop that may not happen at all | W2-RULINGS, John, 21 Sep |
| 8.7 | Slot register rebuilt, 23 slots | |

## The bridge chart, checked on the build, and one label the controller should look at

`app/methodology_page.py` draws the bridge from the last forecast (`_bridge_from_fc`), so it
exists and the host's walk-through is real. Its bars, in order, are Measured market, Capture
share, Coverage, Stimulation, Feed behind, Feed beyond, Aircraft cap where the cap binds, and
Forecast. Section 7.6 gives the host one sentence for each.

Three labels do not read to a lay visitor as they stand, and the controller asked to be told:

1. **"Coverage, x1.12 measured gross-up".** "Gross-up" is a modeller's word. What it means is
   what the booking data misses in this market. The host now says that; the chart still says
   gross-up.
2. **"Forecast, carried, each way / year".** "Carried" and "each way" are the two words a visitor
   most often reads wrongly, and the each-way basis is exactly what Jol caught on the SJC packs
   in August. The host states the basis out loud, but the label is doing important work in five
   words.
3. **"Capture share, 38.2% by schedule quality"** reads as though schedule quality is the only
   input, when frequency, journey time and connection type all score.

W4 proposes nothing in code: these are W1 and W3 surfaces, not W4's, and the freeze is 10
October. Reporting them is the whole of W4's action.

## The three questions, unchanged and now umbrella item 34

1. A second and a third phone contact who can reach the workstation.
2. John's hours on the stand and his five meeting slots.
3. Approve or rewrite the competitor sentence in 4.4.

Nothing else is blocked on John. The two slots he told W4 to keep open, items 25 and 34, are
marked as such, and item 25 is flagged in the manual as the priority slot because Suzanna named
the accuracy question as the one she most expects.

## Watchpoints

1. **The two spend questions name data suppliers.** Pricing 7 puts "what do you pay for OAG,
   Cirium or RDC" on the feedback card. One of those names is read by some buyers as an analytics
   competitor rather than a data supplier, and the manual otherwise says nothing about any
   competitor. W4 has written the question as "what do you pay today for your data
   subscriptions", which gets the same answer without a name crossing the host's lips.
   Controller to confirm, or to rule the named version and W4 will use it.
2. **The manual now depends on a screen that is changing.** Suzanna's answer 2 says the OUTPUT,
   OPTIMISE and RUN ASSESSMENT row does not read clearly, and W2 is changing it. The manual's two
   button sentences carry a slot and follow the screen; if W2 ships different words after the
   manual goes to print, the printed copy is wrong on the one thing she asked about.
3. **The recording may not happen, and the manual has to survive either answer.** Section 8.6 is
   written so that nothing else changes if John's noisy-room test fails. If it goes ahead, the
   notice and the spoken line are W2's to confirm and W9's exhibitor rules gate them.
4. **Her Optimise concern is answered by numbers she has not seen.** She would talk about
   Optimise rather than demonstrate it, on a build that took 196 seconds. It now takes 35 to 65.
   She sees that for the first time at the 16 October trial, which is five days before the show;
   an earlier session on the frozen build would be worth more than the manual is.
5. **Someone edited STAND-HOST-MANUAL.md outside this chat**, correcting the stand number to
   F124. The correction is right and matches the rulings. Noted only because the README says
   nobody edits another workstream's file, and a silent edit to a file two people are writing is
   how a printed copy ends up disagreeing with itself.

## Dates

Training 14-16 October, remote, on the frozen build; dry run 16 October with Jol. v3 after the
8 October screenshots and W5's known-issues list of 1 October. Word copy for print after that,
Avia Solutions as author, en-GB, A4; it cannot go to press before the screenshots and slots 1
and 4 to 8 land. Suzanna lands Tuesday 20 October; setup that afternoon; stand F124 live
Wednesday to Friday.

## Commits landed

`4c0d883`, 19 September, manual v1 and W4-STATUS v1 (John's paste). This session's work is
uncommitted until the block below runs.
