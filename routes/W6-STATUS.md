# W6 status: messaging, marketing, website, meetings

W6 writes this file and rewrites it each session; the controller reads it and never edits it.
Version 5, 20 September 2026, 00:25. Author: Avia Solutions. Version 5 replaces the earlier
versions of the same night, after John's rulings on the site, the domain, the copy owner,
pricing and building the Observatory site like the Avia site, and after the first changes were
made to that site.

Read at session start: routes/README.md; W6-RULINGS.md v1; GTM-STRATEGY-ROUTES-2026.md
(Status, Decisions log, Waiting on John, section 4); ROUTES-COMMERCIAL-PLAN-19Sep2026.md 1-2
and 7-10; ROUTES-CONTROLLER-QUEUE-19Sep2026.md section B; PRICING-HANDOVER-19Sep2026.md;
ROUTES-ATTENDING-ORGANISATIONS-21Sep2026.md; PROMPT-for-Fable-Routes-19Sep2026.txt;
MASTER-TASK-LIST.md 1.6 and 1.7. Cross-workstream facts quoted from W2-STATUS.md v6,
19 September 2026, 20:50. Also read, and now edited, after John's answers: the Observatory site repository at
`E:\Avia\Observatory Website`. No git command has been run from this chat, on that repository
or any other; every commit and push is a block John runs.

## State by scope item

| # | Item | State | Evidence | Next action |
|---|---|---|---|---|
| 1 | Messaging, four sentences | Drafted, waiting on John | W6-MESSAGING-VARIANTS-19Sep2026.md: 3 variants of the one-liner, 3 per sub-message, 2 of the offer; accuracy line verbatim; sentence 3 now carries the pricing ruling, so it is spoken at the stand and published in November | John picks by 25 Sep |
| 2 | Five invitations | Drafted, blocked on contacts and one route | W6-INVITATIONS-AND-MEETINGS-19Sep2026.md: five paragraphs, a proposed pre-run route each with its basis stated | Contacts from John or Suzanna; unserved check on the five routes; send 26-29 Sep |
| 3 | Marketing calendar | Drafted for approval; post 1 and the list email written | W6-MARKETING-CALENDAR-19Sep2026.md | John settles the chart question; out 24-25 Sep |
| 4 | Website | Plan settled at v4; the repository is on GitHub and the launch switch is built | W6-WEBSITE-LAUNCH-PLAN-19Sep2026.md v4: 22 pages reviewed by name, exact takedown list, deployment recommendation, parity list, dates. `Aviaacct1/tao-website` pushed at `2df95ee`. Launch switch proven by two scratch builds | John runs the launch-switch commit block; then the Pages project, then the copy |
| 5 | Meetings logistics | In progress | Schedule, per-meeting owners and dates, pack list, in the invitations file | Firm the slots once the five replies land |

**Commits landed this session.** `8afbe56` on `Aviaacct1/Meridian`, pushed, from John's paste:
"W6 session 1: messaging variants, five invitations, marketing calendar, website launch plan",
4 files changed. Six paths were staged, so at least one W6 file is not in that commit: the
launch plan was still being written to when the block ran, and it shows as modified afterwards
in John's transcript. The remainder goes in a second commit,
`COMMIT-MSG-19Sep2026-w6-v4.txt`, and the hash is recorded here next session.

**`tao-website` is on GitHub, and the Observatory site exists in more than one place for the
first time.** `Aviaacct1/tao-website`, private and empty, created 19 September in John's
browser with his approval, owner and settings checked before and after; then pushed from
`E:\Avia\Observatory Website`: 600 objects, `master` tracking `origin/master`, HEAD
`2df95ee`. It took three attempts, and the two failures are worth keeping: git refuses a
repository on `E:` until the path is added to `safe.directory`, because that filesystem does
not record ownership, and "Repository not found" on a private repository means the repository
is missing or invisible to the credential, not that the credential is wrong. `git ls-remote`
against `Aviaacct1/Meridian` proved the credential before anything else was changed.

**The launch switch is built, proven and LANDED:** commit `e02dd1b` on
`Aviaacct1/tao-website`, pushed, on the renamed branch `main`. With the repository
backed up, W6 made the first changes to it: `src/_data/env.js` reading `SITE_URL` and
`SITE_ENV`, generated `robots.txt` and `_headers` in place of the static file, the noindex tag
and the pre-launch banner made conditional, `site.siteUrl` replaced by `env.url` in twelve
templates so no template holds a domain, `wrangler.toml` for Cloudflare Pages, and the config
moved to CommonJS, which matches the Avia site and removes the Node warning. Proven by two
clean builds to a scratch directory, 25 files each: staging carries the noindex tag, the
banner, `Disallow: /` and the `X-Robots-Tag` header; production carries none of them and reads
`https://aviationobservatory.com` in its canonicals and sitemap. The site now launches on one
variable, as the rulings assumed it already did. The static `src/robots.txt` went with the
same commit, and `master` was renamed to `main` to match the Avia site. One step is left on
GitHub: the default branch there still reads `master`, and the old branch is still present. Two corrections to the record while there:
`_site/` is gitignored, so there is no built copy to clean up in the takedown, and the deploy
rebuilds from source.

**Branch parity DONE.** The Observatory repository is on `main`, matching the Avia site, whose
editor, Pages build and `wrangler.toml` all name a branch. GitHub's default for the repository
was switched from `master` to `main` and the old branch deleted, in John's browser with his
approval, 20 September. Nothing was lost: `master` pointed at `2df95ee`, which is an ancestor
of `main`, so its history is carried in `main` and the branch can be recreated with one
command if anyone wants it. The Pages project can now be wired to `main` without pointing at a
branch nobody pushes to.

**The clean build passed.** `npm ci` then `npx @11ty/eleventy` wrote 23 files in 0.54 seconds
on Eleventy 3.1.6, from John's paste. Node warned `MODULE_TYPELESS_PACKAGE_JSON` and reparsed
`eleventy.config.js` as an ES module, which works but carries the warning into any hosted
build. The fix is one line, `"type": "module"` in `package.json`, and W6 will make it as the
first change after the repository has a remote. No edit goes into a repository that has only
one copy of itself.

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
5. **Pricing is held until November.** The grid does not go on the site before Routes.
   Suzanna states the number in person when asked, in the published wording and no other; she
   says nothing about an overage rate or a discount, because neither exists; and it goes to
   the visitor in writing within 48 hours in the follow-up one-pager. The grid is published in
   November with the order-ready milestone. W4's host manual takes that wording verbatim, in
   place of "on request, limited places", and every price now comes off the site before
   launch as a certainty rather than a condition.
6. **The Observatory site is built to work identically to the Avia site**, so that two sites
   do not become two ways of working. Launch plan section 7 lists what that contains item by
   item: Cloudflare Pages with `wrangler.toml`, the `SITE_ENV` and `SITE_URL` pattern in place
   of the hardcoded noindex tag, a preview environment, the push script, the Sveltia editor
   reusing the same auth Worker and Access policy, the normaliser and its round-trip test, and
   a Pages Function for the forms. All of it before cutover except one part: the page prose
   lives inside the templates, so body-text editing waits for November, and until then the
   editor shows headings and search-engine fields, which is what the Avia editor already does
   for its generated pages. Jol learns one editor either way.

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
3. **The pricing position was not consistent across documents, and John has now settled it.**
   The commercial plan section 5 says a soft figure and never a price on the stand; the
   pricing note has the grid published on the site; the W6 rulings have it published on John's
   sign-off. The ruling of 19 September replaces all three: held until November, stated in
   person by the host, written in the follow-up. W4's host manual and the W5 one-pager both
   change, and the umbrella should record it.
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
4. **The prices are in seven source files**, not the four the pricing note records, and in an
   eighth place no document names: the Meridian page's own `description` front matter ends
   "£15,000 to £25,000 a year by airport size", which is what a search result prints.
5. **The site carries no accuracy claim at all**, so the ruled line is new work on the
   Meridian page, not a check.
6. **The Eleventy config uses `export default` while `package.json` sets no `"type":
   "module"`.** It builds in place today. It must be proven on a clean clone before any hosted
   build is trusted.

## What W6 needs from John

1. **The repo push**, this week: the block is with John. Nothing else in the plan can start
   until `Aviaacct1/tao-website` exists and the clean build is proven.
2. **Access for the editor.** Standing up Sveltia on the Observatory site needs the OAuth app
   and the auth Worker at auth.aviacortex.com pointed at the second repository, and the
   "meridian" Access policy attached to the new `/admin`. Both are John's dashboard, ten
   minutes, and W6 will write the steps.
3. **The chart for post 1**, by 23 Sep. Silence: BRS-EWR.
4. **The five contacts**, by 25 Sep, so the invitations go 26-29 Sep.
5. **The Dallas Fort Worth route.** No public statement of their target list was found; W6
   will not invent one and the draft asks them to name it.
6. **Offer numbers and tier shape** (umbrella items 6 and 7). Not needed before Routes now
   that pricing is held, but sentence 3 cannot be written out in full until they land, and
   the November page waits on them.
7. Access to `C:\src\avia-website` granted 19 Sep; the editor's configuration is read and the
   findings are in launch plan section 7. No further access needed., so W6 can read the editing tool's configuration and
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
