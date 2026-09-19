# W6 status: messaging, marketing, website, meetings

W6 writes this file and rewrites it each session; the controller reads it and never edits it.
Version 3, 19 September 2026, 22:45. Author: Avia Solutions. Version 3 replaces versions 1 and
2 of the same evening, after John's rulings on the site, the domain and the copy owner.

Read at session start: routes/README.md; W6-RULINGS.md v1; GTM-STRATEGY-ROUTES-2026.md
(Status, Decisions log, Waiting on John, section 4); ROUTES-COMMERCIAL-PLAN-19Sep2026.md 1-2
and 7-10; ROUTES-CONTROLLER-QUEUE-19Sep2026.md section B; PRICING-HANDOVER-19Sep2026.md;
ROUTES-ATTENDING-ORGANISATIONS-21Sep2026.md; PROMPT-for-Fable-Routes-19Sep2026.txt;
MASTER-TASK-LIST.md 1.6 and 1.7. Cross-workstream facts quoted from W2-STATUS.md v6,
19 September 2026, 20:50. Also read, after John's answer: the Observatory site repository at
`E:\Avia\Observatory Website`, read only, no git run from this chat.

## State by scope item

| # | Item | State | Evidence | Next action |
|---|---|---|---|---|
| 1 | Messaging, four sentences | Drafted, waiting on John | W6-MESSAGING-VARIANTS-19Sep2026.md: 3 variants of the one-liner, 3 per sub-message, 2 of the offer; accuracy line verbatim; sentence 3 hold condition revised for the pricing question | John picks by 25 Sep |
| 2 | Five invitations | Drafted, blocked on contacts and one route | W6-INVITATIONS-AND-MEETINGS-19Sep2026.md: five paragraphs, a proposed pre-run route each with its basis stated | Contacts from John or Suzanna; unserved check on the five routes; send 26-29 Sep |
| 3 | Marketing calendar | Drafted for approval; post 1 and the list email written | W6-MARKETING-CALENDAR-19Sep2026.md | John settles the chart question; out 24-25 Sep |
| 4 | Website launch plan | v3, rewritten against the real repository and John's three rulings | W6-WEBSITE-LAUNCH-PLAN-19Sep2026.md v3: 22 pages reviewed by name, exact takedown list, deployment recommendation, dates | John rules on pricing and on W6 editing the site repo; the repo goes to GitHub this week |
| 5 | Meetings logistics | In progress | Schedule, per-meeting owners and dates, pack list, in the invitations file | Firm the slots once the five replies land |

Commits landed this session: none. The commit block is with John; the hash goes here next
session. Commit message file: `COMMIT-MSG-19Sep2026-w6-session1.txt`.

## John's rulings taken this session, for the controller's sweep

1. The site to launch is The Aviation Observatory site, not the Avia Solutions site.
2. The domain is aviationobservatory.com. The .aero name in the repository is dropped.
3. Jol is not writing copy at present. W6 prepares the site on our view of what is needed,
   John approves, Jol proofs later. Nothing waits on Jol.
4. John asked whether to deploy the site ourselves, possibly from the workstation. W6's answer
   is in launch plan section 3: deploy it ourselves, on Cloudflare Pages from the repository,
   not from the workstation, with the packs staying on the workstation tunnel. The draft Avia
   site is served from the workstation behind Cloudflare today, which is the right pattern for
   a private draft; W6's objection is only to serving the public site from the machine that
   runs the stand during the show.
5. John asked whether the website editing tool built for the Avia site can also edit the
   Observatory site, so Jol learns one way of working. W6's answer: yes, and after Routes.
   The reasoning is in launch plan section 7.

## Conflicts seen

Reported here for the controller to resolve in the umbrella and the rulings files. W6 has
edited nobody else's file.

1. **W6-RULINGS scope item 4 describes the wrong site.** "Site lite", the five pages that
   matter, "mid-rewrite by Jol", "the IT firm has not launched it" and
   "SITE_ENV=production is the one switch" all describe the Avia Solutions site
   (`avia-website`). The site John has now confirmed is the Observatory site, where none of
   those five statements holds. The dependency line naming `Aviaacct1/avia-website` is
   likewise the wrong repository; the naming register settles this one as `tao-website`.
2. **The IT firm is no longer on the W6 path.** The rulings make them the cutover owner. On
   the recommendation in launch plan section 3 they are not needed for this site at all.
3. **The pricing position is not consistent across documents.** The commercial plan section 5
   says a soft figure and never a price on the stand; the pricing note has the grid published
   on the site; the W6 rulings have it published on John's sign-off. W6 recommends a fourth
   position, spoken by the host and written in the follow-up, and published in November.
   Whichever John picks, W4's host manual and the one-pager both change.
4. **The chart ruled for post 1 conflicts with a standing instruction.** The rulings name the
   SJC-TPE curve. That route came out of Avia's San Jose work, and the standing rule is that
   demo and marketing material never uses an airport Avia has worked for, because targets were
   given in commercial confidence. W6 proposes Bristol to Newark, already run cold on the
   current build on 19 September.
5. **Decision 7, the pack host, is W6's and is now answered** (launch plan section 3 step 5),
   ahead of its 1 October date. W2-STATUS v6 item 6 records it as undated; it now has a date
   and an owner for the mechanics.

## Found this session, not in any document

1. **The Observatory site repository has no git remote.** `.git/config` holds `core` and
   `user` only: no origin, no push, one copy on `E:`, last commit 3 August 2026. Twenty-two
   pages on the critical path to Routes, in a single local folder. First job this week.
2. **The domain in the repository was never the one we own.** `site.json` pointed at an
   unsecured .aero name; John has ruled aviationobservatory.com, which is the name W2 verified
   for mail on 19 September.
3. **The competitor is named in the header and the footer**, so on all 22 pages. Eight source
   files.
4. **The prices are in seven source files**, not the four the pricing note records.
5. **The site carries no accuracy claim at all**, so the ruled line is new work on the
   Meridian page, not a check.
6. **The Eleventy config uses `export default` while `package.json` sets no `"type":
   "module"`.** It builds in place today. It must be proven on a clean clone before any hosted
   build is trusted.

## What W6 needs from John

1. **The pricing ruling**, launch plan section 2. Silence to 26 Sep: W6 builds to the
   recommendation, the grid stays off the site and the host states it verbally.
2. **Whether W6 edits the `tao-website` repository directly**, committing through a block John
   runs, or drafts copy under `C:\AviaDev\routes\` for someone else to apply. W6 recommends
   the first. Silence to 23 Sep: W6 prepares the copy as files in the site repository's own
   structure and commits nothing until John says.
3. **The repo push**, this week: the block is with John.
4. **The chart for post 1**, by 23 Sep. Silence: BRS-EWR.
5. **The five contacts**, by 25 Sep, so the invitations go 26-29 Sep.
6. **The Dallas Fort Worth route.** No public statement of their target list was found; W6
   will not invent one and the draft asks them to name it.
7. **Offer numbers and tier shape** (umbrella items 6 and 7), which sentence 3 waits on
   whichever way the pricing ruling goes.
8. **Access to `C:\src\avia-website`**, so W6 can read the editing tool's configuration and
   say whether it takes a second site without a content refactor. Requested 19 Sep.

## Dependencies on other workstreams

- W1: the chart image from the current build for post 1; pre-warm of the five meeting routes
  by 19 Oct.
- W2: the zone move to Cloudflare, recreating the four Postmark records, week of 22 Sep; then
  the pack hostname on the workstation tunnel and the URL controls, by 8 Oct.
- W3: the PDF render by 8 Oct for post 3 and the printed meeting packs; the Meridian page
  chart.
- W4: the host manual changes if John rules as launch plan section 2 recommends.

## Risks W6 is carrying

1. Twenty-two pages of website in one local folder with no remote. Everything else in this
   plan assumes that folder survives.
2. The zone move touches records that Postmark verified on 19 September while the account is
   still in test mode. Doing it in the week of 22 September rather than the cutover week is
   the mitigation, and Postmark verification is re-checked immediately after.
3. Removing the competitor from a live navigation is an eight-file change plus a rebuild. W6
   wants it done by 8 October, separately from the cutover.
4. The offer has no numbers, so the one-pager left behind at five meetings does not exist.
5. Five invitations name routes not yet checked against OAG for whether they are flown today.
   That check happens before sending.
6. The editing tool saves straight to main on the other site. Pointed at a live Observatory
   site, one stray save republishes it, including during the show. Any editor route needs a
   review branch and a preview first, which the master task list already calls for.
