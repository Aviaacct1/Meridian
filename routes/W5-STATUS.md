# W5 order-ready documents: status

Version 1, 19 September 2026. Written by the W5 chat for the programme controller; rewritten
each session, never appended. W5-RULINGS.md v1 read and acted on. W5 writes no code and edits
no other workstream's file.

READ AND CONFIRMED: W5-RULINGS.md; GTM-STRATEGY-ROUTES-2026.md (Status, section 3, Waiting on
John); ROUTES-COMMERCIAL-PLAN-19Sep2026.md 5 and 6; HANDOVER-ROUTES-19Sep2026.md 7;
PRICING-HANDOVER-19Sep2026.md in full; routes\W2-STATUS.md v6;
PROMPT-for-Fable-Routes-19Sep2026.txt; MASTER-TASK-LIST.md 1.3, 1.5, 2.1 to 2.4, 5.7.

HEAD: the mounted DevPC clone reads `a2c96a7` with a dirty tree. John: run the block at the
foot of this file and paste the HEAD it prints, so W5 knows what it committed on to.

## State, by scope item

| # | Item | State | Evidence | Next |
|---|---|---|---|---|
| 1 | Two-page agreement | DRAFTED v0.1 | `W5-AGREEMENT-19Sep2026.md`, `Meridian-Licence-Agreement-DRAFT-v0.1.docx`, 15 slots, 8 lawyer flags, 3 pages with the markers in and circa 2 without | John answers 1, 2, 3, 6, 7, 11 below; to the solicitor 3 Oct |
| 2 | Invoice template, 30 days, sterling, VAT exclusive | NOT STARTED | | Next session; needs facts 1 and 9 |
| 3 | Onboarding script, 45 minutes | NOT STARTED | | Next session, no dependency |
| 4 | Known-issues list | NOT STARTED | Base is `TESTERS-KNOWN-ISSUES-23Aug2026.md` plus day-of-week, fare, the uncostable types | Draft 1 Oct, frozen 10 Oct, plus whatever Routes exposes |
| 5 | Feedback card and pack-email line | DRAFTED | `W5-FEEDBACK-CARD-19Sep2026.md` | To Jol by 8 Oct; W2 holds the same five questions behind the capture form |
| 6 | Support arrangement | BLOCKED ON JOHN | | Fact 6 below |
| 7 | Licence record, OAG and Sabre | NOT STARTED | | One-page form next session; only John holds the content, fact 10 |
| 8 | Follow-up sequence and one-pager | ONE-PAGER DRAFTED | `W5-ONE-PAGER-19Sep2026.md`, `Meridian-Launch-Customer-One-Pager-DRAFT-v0.1.docx`, 1 page | The 48-hour and two-week sequence next session |

Every Word file is built by `build_w5_docs.py`, which verifies after each build: Avia Solutions
as author and last-modified-by, en-GB at the document default, no other language anywhere, no em
or en dash in the file. Both files pass.

## The tier question, put crisply

The published grid prices by airport size only: £15,000, £20,000 and £25,000 a year, three
seats, 100 presentations, consultancies and groups quoted on portfolio. The commercial plan has
Airport, Airline and Adviser tiers instead.

W5 recommends the published grid, with airlines and advisers named as quoted. The grid is
already printed on the staging site, so a prospect who reads the site and then the one-pager
must see the same numbers or ask which is real; and no airline or adviser price exists to print.
The cost of that choice: an airline planner reads a page priced by airport size and has to be
told his tier is quoted. Silence to 3 October: the published grid.

## Facts only John can supply, numbered

1. **The contracting entity**: Avia Solutions Limited or The Aviation Observatory Ltd, with
   registered number and office. It decides who invoices, who holds the OAG and Sabre
   subscriptions and who carries the liability. No fallback; it is answered before the draft
   reaches the solicitor.
2. **The launch offer**: year-1 discount, number of places, expiry date. Silence to 3 October:
   clause 5 and the one-pager sentence come out and the answer stays "on request, limited
   places".
3. **The presentation overage rate**. No figure exists anywhere; the pricing note says it must
   be set before the first licence is issued. Silence: the 100 included becomes a cap and
   further presentations are quoted one by one, which is a weaker product.
4. **The internal size thresholds** that put a client in the £15k, £20k or £25k step. The
   public policy is settled, the thresholds never were. Needed to write a quotation.
5. **Tier shape**, as above. Silence to 3 October: the published grid.
6. **Support**: the address, the person who reads it every working day, and the response time
   the agreement promises. Silence: one working day, but the name has no fallback and the
   promise is worth nothing without it.
7. **Term**: confirm year 1 does not renew automatically, and give the year-2 loyalty discount
   or rule that year 2 is quoted at list.
8. **The review call**: the draft promises one a quarter with an Avia director. Confirm both.
9. **Invoice detail**: VAT number, bank details, whether a purchase order is required, and the
   numbering. Follows fact 1.
10. **The licence record**: the dates, the participants and what was said on the OAG and Sabre
    calls. Only John and the witnesses hold it; it is what stands in until the letters arrive.
11. **The solicitor**: who, and when he wants the draft with them. W5 targets 3 October so the
    whole of October is available.
12. **Who signs off the known-issues list** before it goes to a client. W5 proposes Nick.

## Watchpoints

1. **The accuracy line and umbrella item 25.** The agreement states the ruled sentence and
   nothing beyond it, and says separately that every forecast carries its own calibrated range.
   It does not say the forecast on the client's screen is 89% within 20%, because that is what
   item 25 is still deciding. If John rules (a), wire BT2 beside the QSI forecast, clause 8
   stays as drafted. If the ruling goes further than the sentence, W5 rewrites clause 8.
2. **Clause 7 is the exposure.** Avia sells outputs from data it licences from OAG and Sabre on
   verbal permission. Until the letters arrive, the record in item 7 is the whole paper trail.
   The solicitor sees this clause first.
3. **Data handling against the usage-data asset.** The agreement says Avia stores no client
   data and stores the outputs, the routes run and the user who ran them. That is the honest
   description of what W2 is building for attribution, and it is what master list 5.7 would
   later commercialise. A client who reads clause 10 and then hears about usage analysis must
   find the two consistent, so 5.7 stays parked until the first client has signed.
4. **The one-pager quotes prices.** The staging site's grid carries a provisional banner and
   the pricing note lists a final commercial sign-off as outstanding. The one-pager prints the
   same numbers without a banner, because a buyer cannot act on a provisional figure. John's
   sign-off on the grid is therefore due before the first one-pager goes out, not before Routes.

## Commits

Nothing landed yet. The block below is the first. Run it on the DevPC and paste the HEAD.
