# W6 status: messaging, marketing, website, meetings

W6 writes this file and rewrites it each session; the controller reads it and never edits it.
Version 6, 20 September 2026. Author: Avia Solutions. Session 2.

Read this session: routes/README.md; W6-RULINGS.md v2 in full, including the four rulings of
20 September (order-ready 21 October; pricing decoupled; the launch offer; item 28 closed).
Cross-workstream facts quoted from W2-STATUS.md v6, 19 September 2026, 20:50. The Observatory
site repository is read and edited; no git command has been run from this chat, on any
repository. Every commit and push is a block John runs.

## What the controller asked for after session 2

**1. The repository push, confirmed.** Remote `https://github.com/Aviaacct1/tao-website.git`,
private. HEAD at session start `e02dd1b` on branch `main`, tracking `origin/main`. The
repository was created and pushed on 19 September (600 objects, `2df95ee`), the launch switch
landed at `e02dd1b`, and the default branch on GitHub was moved from `master` to `main` with
the old branch deleted. Nothing was lost: `master` pointed at `2df95ee`, an ancestor of `main`.

**2. The competitor and price removals, as a file list. LANDED at `6d153d2`**, pushed to
`origin/main` on `Aviaacct1/tao-website`: "Competitor out of the build, prices held until
November, accuracy line on the Meridian page". The file lists below are what that commit
contains. The clean-clone proof is still owed: it clones what is now on GitHub, builds it, and
counts occurrences of the competitor's name and of the price figures in the built output, both
of which must be zero.

Competitor, nine changes:

| File | Change |
|---|---|
| `src/compare/meridian-vs-paxup/` | Moved out of the build to `withheld/compare/`, so it renders nowhere. The file is intact if the content is ever wanted; `git rm -r withheld/` removes it outright, John's call |
| `src/_includes/partials/header.njk` | Navigation entry removed, and the `/compare/` case dropped from the Products current-page test |
| `src/_includes/partials/footer.njk` | Footer link removed |
| `src/insights/index.njk` | Comparison card and its read link removed |
| `src/insights/what-is-a-route-forecasting-tool/index.njk` | Named in the lede, in the FAQ JSON-LD answer and in the closing paragraph. All three gone; the paragraph now points at the Meridian trial alone |
| `src/products/index.njk` | The FAQ row asking how Meridian compares, removed |
| `src/products/meridian/index.njk` | The compare button removed |
| `src/legal/index.njk` | Named in the third-party marks line. Removed. Boeing, Airbus, the CMO and the GMF stay: they are the forecasts the Global Forecast is scored against on its own page, not a competitor to Meridian, and removing them would break the peer-set claim |
| `src/sitemap.njk` | Nothing to change; the URL leaves the sitemap because the page leaves the build |

Prices, eight files, held until November:

| File | Change |
|---|---|
| `src/_data/site.json` | Every figure removed from the pricing block; seats, presentations and the tier labels stay, with a note in the file saying why and until when |
| `src/pricing/index.njk` | Meta description, two FAQ answers in JSON-LD, the lede, the summary paragraph and four price tiles. The page keeps its structure, its tiers and its licence shape, and says prices are published in November 2026 |
| `src/products/meridian/index.njk` | Meta description, three `Offer` entries in the SoftwareApplication JSON-LD, the priced FAQ answer, the priced prose and the trial paragraph |
| `src/products/observatory-global-forecast/index.njk` | Meta description, the `Offer` in the JSON-LD, the trial paragraph and the licence sentence |
| `src/products/index.njk` | The hero stat "£15-25k a year, published" becomes "100 presentations a year" |
| `src/index.njk` | The home page's priced licence sentence |

The eighth place was the Meridian page's own `description` front matter, which no document
named and which is what a search result prints. It is in the list above.

**Proven, not assumed.** Two builds from the edited tree, 24 pages each. In the production
build: zero occurrences of the competitor's name in any file, zero price figures in any file,
no comparison URL in the sitemap, the accuracy line present on the Meridian page verbatim, no
noindex on any page, robots.txt allowing with the sitemap line. In the staging build: noindex
on all 22 page files, `Disallow: /`, and the `X-Robots-Tag` header. The clean-clone proof the
controller asked for is the block John runs after the commit, because this chat runs no git.

**3. Invitations updated.** All five now say "the pack follows the same day" wording where
the promise appears, and each carries one added sentence: launch terms can be put in front of
them at the meeting, they close on 30 November, and an agreement and onboarding are ready
immediately after the show. The meetings logistics carries order-ready at 21 October. Item 28
is closed, so post 1 uses the SJC-TPE curve as first ruled and the BRS-EWR alternative is
dropped; post 1 and the list email can go to John for approval now.

## State by scope item

| # | Item | State | Evidence | Next action |
|---|---|---|---|---|
| 1 | Messaging | v2, sentence 3 rebuilt as the launch offer | W6-MESSAGING-VARIANTS v2: three variants of the offer carrying the steps and not the pounds; sub-message 2.2 moved to "the same day" | John picks by 25 Sep |
| 2 | Five invitations | v2, ready to send | Launch-terms sentence in all five; pack promise corrected | Contacts from John or Suzanna by 25 Sep; unserved check on the five routes; send 26-29 Sep |
| 3 | Marketing calendar | Post 1 and the list email ready for approval | Chart ruled: SJC-TPE. Offer deliberately absent from both | John approves; out 24-25 Sep |
| 4 | Website | Removals landed at `6d153d2`, pushed | File lists above; two builds before commit | The clean-clone proof, then the Pages project once W2 moves the zone |
| 5 | Meetings logistics | Updated for order-ready 21 Oct | One-pager row now carries the ruled offer | Firm slots when the five reply |

## Conflicts seen

1. **The site's candour line.** The pricing page's lede said the prices are printed because an
   institution that publishes its errors can publish its prices. With the figures held until
   November, that sentence cannot stand as written. W6 has changed it to say the prices will
   be published, in November, rather than deleting the position. It is John's sentence
   originally and he may want different words.
2. **The pricing page stays in the navigation** with its tiers and licence shape and no
   figures. W6 recommended removing it from the navigation in the plan; on reflection, sales
   is led by written quotation, so a page that explains the licence and says when prices
   publish is more use than a gap. Easy to reverse either way.
3. **"Quoted" now appears where three prices were.** That is honest and it is the agreed
   channel, but a visitor sees three tiers with the same word in each. In November the figures
   drop back into the same slots.

## What W6 needs from John

1. **The five contacts**, by 25 Sep, so the invitations go 26-29 Sep. Still the only thing
   blocking the invitations.
2. **The four sentences settled**, by 25 Sep, including which offer variant the host uses.
3. **Approval of post 1 and the list email**, which have nothing left waiting on them.
4. **The Dallas Fort Worth route.** No public statement of their target list was found; the
   draft asks them to name it. Overrule if John knows it.
5. **Item 6 by 3 Oct**: number of launch places, overage rate, payment terms, size thresholds,
   and which entity contracts. The offer sentence works without them; the agreement does not.
6. **Whether `withheld/compare/` stays in the repository** or is removed outright.

## Dependencies on other workstreams

- W2: the zone move to Cloudflare in the week of 22 Sep, which the Pages deployment needs;
  then the pack hostname on the workstation tunnel by 8 Oct.
- W3: the SJC-TPE curve image from the current build for post 1, with unit, period, forecast
  and the source line on it; the PDF render by 8 Oct for post 3 and the printed meeting packs.
- W5: the one-pager carries the launch offer in writing, including the year-1 pounds, which
  appear nowhere public.
- W4: the host's price sentence is the steps, never the list, and signing closes 30 November.

## Risks W6 is carrying

1. The Pages project cannot be created until the zone moves, and the zone move is W2's, in the
   week of 22 September. Everything after it on the website dates is compressed if it slips.
2. Five invitations name routes not yet checked against OAG for whether they are flown today.
   That check happens before sending.
3. The launch offer is decided but the agreement it is signed on is W5's, and order-ready is
   now 21 October rather than 7 November, which removes seventeen days from that work.
4. The site now says prices publish in November. That is a public commitment as soon as the
   site is live, and it lands in the same fortnight as the show.
