# W6: the website launch plan

Author: Avia Solutions. Version 1, 19 September 2026. John ruled on 19 September: launch
before Routes, as a site lite if the full site is not ready. This plan says what Jol must
finish, what the IT firm must do, on what dates, and what comes down before anything goes
public. W6 places the pack files once W2 hands over the URL rule. W6 publishes nothing.

---

## 1. One question before the plan can be trusted

The documents name two websites and W6 cannot tell from here whether they are one repository
or two.

- The rulings name **Aviaacct1/avia-website**, cloned on the Dev PC at `C:\src\avia-website`
  (confirmed to exist, 19 September; this chat cannot read it, see below). Master task list
  1.6 and 1.7 describe this one: the admin editor at website.aviacortex.com/admin, 24 pages,
  Jol's access resolved on 1 September, the editor now lists all pages and saves to main.
- PRICING-HANDOVER-19Sep2026.md section 2 puts the price grid, the Meridian page, the
  products stat bar, `src/_data/site.json` and the comparison page in **the Observatory
  website repo at `E:\Avia\Observatory Website`**, with the reasoning in its BUILD-NOTES.md.

The two takedowns in section 4 below live in the second of those. The pages Jol is
rewriting live in the first, on the evidence of the master list. If they are one repository
under two paths, the plan holds as written. If they are two sites, John must say which one
launches before Routes, because the pages that matter for a Routes visitor (Meridian and
pricing) are on the Observatory side and the rewrite is on the Avia side.

**Second question, same size.** Both public names in the documents are
`website.aviacortex.com` and `meridian.aviacortex.com`. The naming ruling is that Avia Cortex
never appears on a client surface. A domain is the most client-facing surface there is. The
site must launch on a name John is content to print on a card: aviasolutions.com,
aviationobservatory.com, or a subdomain of one of them. This decides the DNS work the IT
firm does, so it cannot wait for the cutover week.

**Repository access.** `C:\src\avia-website` is on the Dev PC but is not in the folders this
chat can reach; `E:\Avia\Observatory Website` is on the workstation and is not reachable
either. W6 is asking John for the one that launches, by name, rather than guessing a path.
Until then W6 writes the plan and not the pages.

---

## 2. The pages, the owners, the dates

Site lite. Five pages, plus the two that carry the packs. Q&A is added after Routes from the
questions the stand actually produces, which is the only honest way to write it.

| Page | What must be true at launch | Owner | Copy final |
|---|---|---|---|
| Home | The one-liner and the three sub-messages, as settled on 25 Sep. Stand F174 and the dates, above the fold, until 23 October | Jol writes, John approves | 5 Oct |
| Products, Meridian | What it does, the three classes of number in plain words, the accuracy line verbatim, one real chart from the current build with unit, period, forecast and source on it. A request form that writes to the lead store | Jol writes, W6 supplies the accuracy and chart rules, W5 the form target | 5 Oct |
| About | The rewrite Jol called for on 1 September. Independent since 2001, the work, the people | Jol, John approves | 5 Oct |
| Contact | One form, one address, no telephone routing that nobody answers during the show | Jol | 5 Oct |
| Team | Named people with current titles. John, Jol, Nick, Jess, Suzanna as stand host if John wants her listed | Jol, John confirms every name | 5 Oct |
| Pack pages (hosted packs) | Unguessable URL, noindex header, an expiry, no personal data in the file, content checked against the data position before hosting | W2 owns the rule and the controls, W3 the content check, W6 places the files | 16 Oct |
| Q&A | Not at launch. Built after Routes from the questions asked on the stand | W6 drafts, John approves | Post-show |

Anything not on this list stays unpublished. The master list records that `markets`,
`benchmarks` and `data` have no inbound links; they stay out of the launch build and the
sitemap, and John decides on them after the show.

---

## 3. What Jol must finish, and when

John carries this to Jol. Jol reads on a phone, so it is five lines.

1. Home, products/Meridian, about, contact, team. Copy final by **Monday 5 October**.
2. Nothing else. The other pages stay in the build but out of the sitemap and the navigation.
3. The accuracy sentence on the Meridian page is verbatim and is not edited: W6 supplies it.
4. No price, no discount, no places, no expiry on any page until John signs the grid off.
5. No page mentions any competitor. The comparison page comes out of the build entirely.

If copy is not final on 5 October, the launch still happens on the dates below with the
pages Jol has finished, and the unfinished ones stay out of the navigation. A site lite with
four good pages beats a complete site that misses the show.

---

## 4. The two takedowns, before anything goes public

**Takedown 1: the competitor comparison page.** The page, its entry in the navigation, every
internal link to it, its sitemap entry, and any reference to it from the products or pricing
pages. Nothing about any competitor is published anywhere on the site. This is the 19
September ruling and it is not a judgement call at cutover time. Umbrella item 11 awaits
John's confirmation; this plan is built on withholding the page, as ruled.

**Takedown 2: the price grid and its provisional banner.** Unless John signs the grid off
before the cutover, the published prices come down in all four places the pricing note
records: `/pricing/`, the Meridian page (the lede, the FAQ and the SoftwareApplication
JSON-LD offers at 15000, 20000 and 25000 GBP), the products page stat bar, and
`src/_data/site.json`. The JSON-LD is the one that gets missed, because it is invisible on
the page and visible to everything that reads the page. If John does sign the grid off, the
grid stays and the "provisional, not for publication" banner comes off in the same change,
never one without the other.

A third item, not a takedown but a check with the same weight: the site is noindex
throughout today. At launch, robots, noindex and the security headers all move together on
`SITE_ENV=production`. Somebody checks from outside the network, on a phone, that the pack
URLs are still noindex after the switch. W6 will do that check on the day and record it.

---

## 5. The paragraph for the IT firm

For John to send. One paragraph, one date to confirm.

> We are taking the site live before World Routes, which runs from 21 October, so the cutover
> needs to complete by Wednesday 14 October. Please plan for that week: the production DNS
> change to [DOMAIN], `SITE_ENV=production` so that robots, noindex and the security headers
> all move together, the Cloudflare Access policy removed from the public pages and kept on
> the admin editor, and TLS, redirects and the sitemap checked from outside our network. Two
> pages will be removed from the build before the cutover and must not appear in the sitemap
> or the navigation; we will confirm which by 8 October. A small number of pack pages will be
> added after launch at unguessable URLs, which must carry a noindex header and must stay out
> of the sitemap. Please confirm by 3 October that you can hold 12 to 14 October, and tell me
> what you need from us before then.

---

## 6. The dates, in order

| Date | What happens | Owner |
|---|---|---|
| 22 Sep | John names the repository and the public domain | John |
| 25 Sep | Four sentences settled, so the copy can be written against them | John, Jol |
| 3 Oct | IT firm confirms the cutover window | IT firm, John chases |
| 5 Oct | Jol's copy final on the five pages | Jol |
| 8 Oct | W6 confirms the takedown list to the IT firm; John rules on the price grid | John, W6 |
| 12-14 Oct | Cutover, `SITE_ENV=production`, Access removed from public pages | IT firm |
| 15 Oct | W6 checks from outside the network: pages live, noindex correct, no comparison page, no price if not signed off, forms writing to the lead store | W6, evidence in W6-STATUS.md |
| 16 Oct | Pack hosting live and checked; the URL goes on the cards and the packs | W2, W6 |
| 17 Oct | Content freeze on the site. Nothing changes until after the show | Everyone |

If the cutover slips past 14 October, the fallback is the single public landing page in the
commercial plan section 7, at a public URL outside Access, carrying the Meridian page's
content and the form, and costing about a day. W6 will say on 8 October which of the two is
happening, and will not leave that call to the week of the show.
