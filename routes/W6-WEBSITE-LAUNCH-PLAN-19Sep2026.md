# W6: the website launch plan

Author: Avia Solutions. Version 3, 19 September 2026. Supersedes versions 1 and 2 of the same
date. Written after three rulings from John on 19 September: the site is **The Aviation
Observatory site**; the domain is **aviationobservatory.com**; Jol is not writing copy at
present, so W6 prepares the site on our view of what is needed and Jol proofs later. John also
asked whether we should deploy it ourselves, possibly from the workstation. Section 3 answers
that.

W6 read the repository at `E:\Avia\Observatory Website` on 19 September, read only, and runs
no git from this chat. Cross-workstream facts below are quoted from W2-STATUS.md version 6,
19 September 2026, 20:50.

---

## 1. What the repository actually contains

**1.1 It is a built site of 22 pages, not a site lite.** Products (Meridian, the Observatory
Global Forecast, the design day module), how it works, three method notes, track record,
pricing, three trials pages, documentation, three insights pages, about, contact, legal. The
work before Routes is a review of what exists against the rulings, not the writing of five
pages.

**1.2 It has no git remote.** `.git/config` carries `core` and `user` only. There is no
origin, no push, and one copy of the site on `E:`, last committed on 3 August 2026. The
naming register settles the repo name as **`tao-website`**, so either
`Aviaacct1/tao-website` exists and this clone was never wired to it, or it was never created.
Twenty-two pages of work sitting in a single local folder, now on the critical path to
Routes, is the first thing to fix and it is a ten-minute job.

**1.3 There is no `SITE_ENV` switch.** That belongs to the Avia Solutions site.
Here, `noindex, nofollow` is a hardcoded meta tag at line 9 of
`src/_includes/layouts/base.njk`, under the comment "Staging: names not yet legally cleared.
Remove noindex only at launch sign-off". Launch is an edit and a rebuild: the meta tag comes
out, `siteUrl` in `src/_data/site.json` becomes `https://aviationobservatory.com`, the
`staging` flag goes false, and the analytics are switched on.

**1.4 The domain in the repository is the wrong one.** `site.json` points at
`staging.theaviationobservatory.aero` with a note in the file that the .aero name is not
secured. John has now ruled aviationobservatory.com, which is the name W2 has already
verified for mail. One line changes, and the .aero name is dropped.

**1.5 The competitor is named in the header and the footer**, so it appears on all 22 pages,
not only on the comparison page. Eight source files carry it. Full list in section 5.

**1.6 The prices are in seven source files**, not the four the pricing note records: the home
page and the Observatory Global Forecast page are priced too.

**1.7 The site carries no accuracy claim at all.** The ruled line has to be added to the
Meridian page, with a real chart from the current build. That is new work, and W6 owns the
wording.

---

## 2. Pricing: ruled 19 September, hold until November

John ruled on 19 September: the price grid is held until November. It does not go on the site
before Routes, and Suzanna states the number in person when asked.

What that means in practice, and all three parts are binding:

1. Suzanna says the number out loud when asked, in the published wording and no other:
   £15,000, £20,000 or £25,000 a year by airport size, three seats, 100 presentations
   included, quoted and invoiced. Nobody is refused a number.
2. She says nothing about the overage rate or any discount, because neither exists. If
   pressed: "the rate is stated in the licence, and the quotation confirms the size step."
3. It goes to them in writing within 48 hours in the follow-up one-pager, so five
   conversations do not become five different numbers.

The grid goes on the site in November with the order-ready milestone on the 7th, once the
commercial sign-off that clears the product names has landed, the presentation overage rate
exists, and the launch offer is set. At that point the page carries the whole position rather
than a number with two holes in it, and John's argument of 2 August is honoured in full: an
institution that publishes its error does not hide its prices behind a call.

Two consequences to carry:

- **W4 changes.** The commercial plan section 4 says no price on the stand beyond "on request,
  limited places", and the host manual is being written to that. The wording in point 1 above
  replaces it, verbatim.
- **The site takedown is now certain, not conditional.** Every price on the site comes out
  before launch. The files are in section 5.

---

## 3. Deployment: deploy it ourselves, but not from the workstation

John's instinct to take this in house is right, and it removes the IT firm from the critical
path for this site entirely. They hold the Avia Solutions site; they do not need to touch this
one. W2's experience is the argument: every step of the mail route that needed the Microsoft
365 tenant ran through admin rights John does not hold, three weeks before the freeze
(W2-STATUS.md v6). A static site we deploy ourselves has no such queue in it.

**Not the workstation, though.** During Routes that machine is the single box running Meridian
and Atlas for the stand, unmanned, restarted by remote desktop over Tailscale, and it is the
machine W7's Plan B exists for. Serving the public website from it means a reboot takes the
website down in the middle of the show, and it puts public traffic on the same tunnel
connector that serves the demo. The site is 22 static pages with no database and no server
code; nothing about it wants a workstation.

**W6's recommendation, five steps.**

1. **Create the private repo and push**, this week. `Aviaacct1/tao-website`, the name already
   settled in the naming register. Keep the working copy where it is on `E:` and give it a
   remote and a push script, exactly as the Avia site does with `PUSH-WEBSITE.bat`, so the two
   sites are handled the same way; the alternative, cloning to `C:\src\tao-website`, is
   cleaner on paper but makes the Observatory site the odd one out. Either way the push runs
   from the Dev PC, where the GitHub credentials are. This is worth doing even if every other
   decision changes.
2. **Prove the build on a clean checkout** before trusting any hosted build. `npm ci` then
   `npx @11ty/eleventy`. One thing to watch: `eleventy.config.js` uses `export default` while
   `package.json` sets no `"type": "module"`. It builds in the working folder today; prove it
   builds from a fresh clone, because that is what a hosted builder does.
3. **Move the aviationobservatory.com zone to Cloudflare**, week of 22 September, before any
   web work. The zone is at Fasthosts today and carries exactly four records, all verified by
   Postmark on 19 September (W2-STATUS.md v6): DKIM TXT at
   `20260919185744pm._domainkey`; return-path CNAME `pm-bounces` to `pm.mtasv.net`; DMARC TXT
   at `_dmarc`, `v=DMARC1; p=none`; no SPF record, because Postmark aligns through the
   return-path. Recreate those four, verify in Postmark, and only then touch anything
   web-side. W2 deferred this move because it meant recreating records just verified; the
   website decision now forces it, and doing it in the week of 22 September rather than the
   cutover week is the whole mitigation. It also answers W2's open item 3, the DMARC reports,
   because Cloudflare Email Routing gives the domain an inbound address for free.
4. **Cloudflare Pages, connected to the repo.** Build `npx @11ty/eleventy`, output `_site`,
   deploy on push, certificate automatic, no origin to harden and nothing to keep running.
   The custom domain is attached at cutover, which means the cutover is ours and takes five
   minutes rather than being a date we ask someone else to hold. This is not a new pattern:
   the Avia Solutions site already runs this way. Its `wrangler.toml` sets
   `pages_build_output_dir = "_site"`, `SITE_ENV = "staging"` for the noindex draft,
   `SITE_URL = https://website.aviacortex.com`, a preview environment at
   `review.avia-website.pages.dev`, and a D1 database for the contact form. So the Observatory
   site copies a working arrangement rather than inventing one, and the `SITE_ENV` switch the
   rulings describe is real, on that site, driven by those variables. One correction for the
   record: the Avia draft site is served by Cloudflare Pages, not by the workstation. The
   workstation holds a working copy that pushes with `PUSH-WEBSITE.bat`.
5. **Packs stay on the workstation**, served through the existing tunnel at
   `packs.aviationobservatory.com`, with no Access policy on that hostname, a noindex header
   and an expiry. Adding a hostname to that tunnel is a ten-minute job on the existing
   connector. The packs are generated on that machine, so this avoids an upload step during
   the show. The honest cost: if the workstation is down, the pack link is dead. That is
   tolerable because the PDF is attached to the same email, so a visitor who cannot open the
   link still has the pack. W6 takes this as decision 7 (due 1 October, W2-STATUS.md v6 item
   6); W2 owns the mechanics and the URL rule.

If John prefers the workstation for the site itself, it can be done on the same tunnel in an
afternoon, and W6 will write it up. The recommendation stands against it for the reason in the
second paragraph.

---

## 4. Copy: W6 drafts, John approves, Jol proofs later

John ruled on 19 September that Jol is not writing copy at present. W6 therefore prepares each
page on our view of what is needed, John approves, and Jol proofs when he can. Nothing waits
on Jol. The page review below replaces "what Jol must finish".

| Page | What W6 does | John's part | By |
|---|---|---|---|
| Home | Rewrite the message to the four sentences settled on 25 Sep; add stand F174 and the dates until 23 Oct; remove the price | Approve the message | 5 Oct |
| Products, and products/meridian | Add the accuracy line verbatim; add one real chart from the current build with unit, period, forecast and source on it; remove the compare button; check no feature appears that is not in the frozen build | Approve the page | 5 Oct |
| How it works, three method notes | Reconcile with Nick's methodology note; the 2 July deck and that note are known to differ in four places (W3-STATUS) | Nick reads, John approves | 8 Oct |
| Track record | Check every figure carries a source, and that nothing identifies a client's confidential target | John rules on anything doubtful | 5 Oct |
| Trials, three pages | Make the trial the stand's capture path, writing to the lead store | Approve the wording | 8 Oct |
| Insights, three pages | Competitor out; rewrite the article around what Meridian does | Approve | 5 Oct |
| About, contact, team | Current names and titles; a contact form someone reads during the show | Confirm every name | 5 Oct |
| Legal | Licence wording consistent with the pricing ruling | John, with the W5 licence draft | 8 Oct |
| Pricing | Per section 2 | John rules | 8 Oct |
| Documentation | Nothing published that describes an unreleased feature | W3 checks | 8 Oct |

Q&A is not written before the show. It is built afterwards from the questions the stand
produces, which is the only honest way to write one.

W6 asks one thing here: whether W6 edits the `tao-website` repository directly, committing
through a block John runs like every other workstream, or drafts the copy under
`C:\AviaDev\routes\` for someone else to apply. W6 recommends the first, because twenty-two
pages moved by hand between two repositories is how a page gets missed.

---

## 5. The takedown list, by file

Nothing about any competitor is published. The name is in eight source files, and `_site/` is
committed, so the rebuild is part of the takedown.

| File | What comes out |
|---|---|
| `src/compare/meridian-vs-paxup/index.njk` | The whole page and its permalink |
| `src/_includes/partials/header.njk` | The navigation entry, on all 22 pages |
| `src/_includes/partials/footer.njk` | The footer link, on all 22 pages |
| `src/insights/index.njk` | The comparison card and its read link |
| `src/insights/what-is-a-route-forecasting-tool/index.njk` | Every mention in the article |
| `src/products/index.njk` | The FAQ row asking how Meridian compares |
| `src/products/meridian/index.njk` | The compare button |
| `src/legal/index.njk` | The mention there |
| `_site/` and `src/sitemap.njk` | Rebuilt, with no comparison URL in the sitemap |

**Pricing, if John rules as section 2 recommends.** Seven source files carry prices:
`src/_data/site.json`, `src/pricing/index.njk`, `src/products/meridian/index.njk`,
`src/products/index.njk`, `src/index.njk`, `src/products/observatory-global-forecast/index.njk`,
and the comparison page, which is going anyway. Two of those hide in places a reader does not
see and a search engine does. The first is the SoftwareApplication JSON-LD offers on the
Meridian page, which the pricing note names. The second is not in any document: the Meridian
page's own `description` front matter ends "£15,000 to £25,000 a year by airport size", and a
meta description is exactly what a search result prints. Both come out. The pricing page itself
leaves the navigation and the sitemap rather than standing there with no prices on it.

---

## 6. The dates

| Date | What happens | Owner |
|---|---|---|
| 22 Sep | Repo `tao-website` created and pushed; clean build proven | John runs the block, W6 writes it |
| 22 Sep | Pricing ruled; W6 confirmed as the copy owner | John |
| 23-26 Sep | Zone moved to Cloudflare, four Postmark records recreated and verified | W2, John approves |
| 25 Sep | Four sentences settled, so the copy is written against them | John |
| 26-30 Sep | Cloudflare Pages project created, building from the repo on push; `wrangler.toml` and the `SITE_ENV` pattern copied from the Avia site; push script added | W6 writes the steps, John runs them |
| 30 Sep | Editor stood up: Sveltia config with title and description per page, other keys declared hidden, same auth Worker and Access policy, round-trip test passed | W6, John approves access |
| 5 Oct | Copy final on home, products, insights, about, contact, track record | W6, John approves |
| 8 Oct | Takedown applied and rebuilt: competitor out of eight files, every price out of seven files plus the Meridian page's meta description; method notes checked by Nick; forms given a destination; pack hostname added to the tunnel | W6, W2, W5, Nick |
| 12-14 Oct | Cutover: noindex out, site URL replaced, staging false, analytics on, custom domain attached | W6 writes it, John runs it |
| 15 Oct | W6 checks from outside the network: pages live and indexable, no competitor anywhere including header and footer, pricing as ruled, forms writing to the lead store, accuracy line correct | W6, evidence in W6-STATUS.md |
| 16 Oct | Pack hosting live and checked; the URL goes on the cards and in the packs | W2, W6 |
| 17 Oct | Content freeze. Nothing changes until after the show | Everyone |

The IT firm is not on this path. Nothing on this list needs them, and W6 has withdrawn the
paragraph that version 2 drafted for them. If John wants them told, one line after cutover is
enough.

If the zone move slips past 30 September, the fallback is a single public page on the same
Pages project, carrying the Meridian page's content and the trial form, with the rest of the
site left unpublished. W6 will call that on 8 October and will not leave it to the week of the
show.

---

## 7. One way of working: the Observatory site built like the Avia site

John ruled on 19 September that the Observatory site should work identically to the new Avia
site, so that two sites do not become two ways of working. W6 agrees, and most of it is cheap.
The list below is what "identically" contains, item by item, with what it costs.

**What the Avia site has that the Observatory site does not.**

| Item | Avia site | Observatory site | Cost to match |
|---|---|---|---|
| Host | Cloudflare Pages, `wrangler.toml`, output `_site` | Nothing; no remote at all | Half a day, once the repo is on GitHub |
| Staging switch | `SITE_ENV` and `SITE_URL` as Pages variables, read at build by `src/_data/site.js` | `noindex` hardcoded in `base.njk`, `siteUrl` hardcoded in `site.json` | An hour. Copy the pattern, and the rulings' "one switch" becomes true here too |
| Preview | A preview environment with its own URL | None | Included with Pages |
| Editor | Sveltia CMS at `/admin`, GitHub backend, auth Worker at auth.aviacortex.com, Cloudflare Access under the "meridian" policy | None | A day, reusing the same Worker and policy; see below |
| Save safety | `tools/cms/normalise.mjs` and a save-without-change round-trip test | None | Copy both, run the test |
| Forms | Pages Function writing to a D1 database | None | Half a day; the trial and contact forms need a destination, and W5 owns where it lands |
| Push | `PUSH-WEBSITE.bat`, pull with rebase then push | None | Ten minutes |
| Cutover record | `CUTOVER.md` | None | Written as we go |

**The editor is cheaper here than it looked, and Jol can have it from the start.** Sveltia
edits declared fields in front matter and data files, and every Observatory page already
carries front matter: `layout`, `title`, `description`, `permalink`, `breadcrumbs`. So a pages
collection that exposes the title and the search-engine description, with the other keys
declared hidden, is configuration rather than a rewrite. That is the same treatment the Avia
config already gives its generated pages, which show their heading and search-engine fields
only and have their bodies built by the site. Jol therefore learns one editor, one sign-in and
one save, and the difference between the two sites is which pages let him edit the body text.

**The one thing that waits for November.** The Observatory pages hold their prose inside the
templates, mixed with tables and JSON-LD, so body text is not editable until it is lifted out
into markdown. That is 22 pages of careful work and it is not going next to the freeze, the
host training and the pack pipeline. It is the November job, and after it the two sites are
the same in every respect.

**The control that makes this safe.** The Avia config states the rule in its own header:
Sveltia writes back only the fields declared and drops the rest. Every front-matter key on
every Observatory page must therefore be declared, hidden where it is not editable, and the
round-trip test run before Jol touches it: open an entry, save it without changing anything,
and `git diff` must be empty. `breadcrumbs` and `permalink` are the two that would be silently
dropped, and losing a permalink changes a page's URL.

**And the branch.** The Avia editor commits to `main`, which John decided on 1 September when
the site was private, behind Access and noindex, with two people editing. Once either site is
public, one stray save republishes it, including during the show. The config's own comment and
the master task list both say to reinstate a review branch with a preview at launch. W6 asks
that this happens at the Observatory cutover on 12 to 14 October, and on the Avia site at its
cutover, rather than after either.

**A document conflict for the master list.** `CMS-README.md` in the Avia repo describes the
editor as reading and writing the `review` branch with a preview, and says editor changes do
not reach the draft site until `review` is merged. `src/admin/config.yml` sets `branch: main`
and records John's decision of 1 September. The README describes a flow the tool no longer
follows, so anyone reading it expects a safety step that is not there.
