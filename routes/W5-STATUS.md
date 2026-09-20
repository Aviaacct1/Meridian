# W5 order-ready documents: status

Version 3, 20 September 2026. Written by the W5 chat for the programme controller; rewritten
each session, never appended. W5-RULINGS.md v2 and routes\README.md v1 read and acted on. W5
writes no code and edits no other workstream's file.

ORDER-READY IS 21 OCTOBER. Every W5 document lands by 10 October, not 3 November. Agreement
and one-pager are v0.2 today, ahead of John's figures on 3 October and the solicitor in the
week of 6 October.

Clone: the mounted DevPC clone reads `702d525`, with the five rulings files modified in the
working tree by the controller. W5 has not run git. The block at the foot is John's.

## State, by scope item

| # | Item | State | Evidence | Next |
|---|---|---|---|---|
| 1 | Agreement | v0.2 TO RULINGS v2 | `W5-AGREEMENT-19Sep2026.md`, `Meridian-Licence-Agreement-DRAFT.docx`, 17 clauses, 9 slots, 13 lawyer flags, 4 pages with the markers in | John's figures by 3 Oct, solicitor week of 6 Oct |
| 2 | Invoice template | NOT STARTED | | Next session; needs facts 1 and 11 |
| 3 | Onboarding script, 45 minutes | NOT STARTED | | Next session, no dependency |
| 4 | Known-issues list | NOT STARTED | Base is `TESTERS-KNOWN-ISSUES-23Aug2026.md` plus day-of-week, fare, the uncostable types. It is now the agreement's schedule, so it is contractual | Draft 1 Oct, frozen 10 Oct |
| 5 | Feedback card and pack-email line | DRAFTED v0.1 | `W5-FEEDBACK-CARD-19Sep2026.md` | To Jol by 8 Oct. Ruling: W5's wording is the only wording, quoted with its version by W4 and W2 |
| 6 | Support arrangement | BLOCKED ON JOHN | | Fact 8 |
| 7 | Licence record, OAG and Sabre | NOT STARTED | | One-page form next session; only John holds the content, fact 10 |
| 8 | One-pager and follow-up sequence | ONE-PAGER v0.2 | `W5-ONE-PAGER-19Sep2026.md`, `Meridian-Launch-Customer-One-Pager-DRAFT.docx`, 2 pages, printed double-sided for the five meetings | The 48-hour and two-week sequence next session |

## The finalisation checklist, item by item

1. **DONE.** Launch offer at 50% / 75% / 85% as three fixed cash figures, rounded to the
   nearest £50, year 4 at the published list. Clause 4 and the one-pager's first table.
   Small £7,500 / £11,600 / £13,550. Medium £10,000 / £15,450 / £18,050. Large £12,500 /
   £19,300 / £22,550.
2. **DONE.** The three-year list table at a flat 3%, labelled for illustration, with the
   contractual mechanism named as clause 5. Clause 4.
3. **DONE.** The banded list quoted as the reference, three seats, 100 presentations, size
   from published passenger numbers in the quotation. Clauses 2 and 4. The internal thresholds
   are fact 4.
4. **DONE.** Add-ons at 50% in year 1 or 75% in year 2; new functions as priced options; a
   core-price increase above escalation where a function is folded into core, on the renewal
   notice, with the right not to renew. Clause 6 and the one-pager.
5. **DONE.** Escalation at not less than UK CPI, ONS all items, twelve months to the preceding
   December, with Avia able to set more in the renewal notice; the launch years as the express
   exception. Clause 5, and one line on the one-pager.
6. **DONE.** Annual automatic renewal, one month's notice from the client, Avia's notices at
   three and two months, the conditional opt-out on a procurement-rules declaration at no
   premium. Clause 3 and the one-pager.
7. **DONE.** Avia ending or suspending: notice, pro-rata refund to the day within 30 days,
   outputs kept, no further liability, the data-licence trigger named expressly. Clause 15.
   The notice period is fact 6.
8. **DONE.** The four launch conditions and the signature deadline of 30 November 2026, in the
   offer and in clause 8, not in the term. The known-issues list is attached as the schedule.
9. **PART.** Clause 7 and the one-pager carry annual in advance, invoice on signature, 14 days,
   VAT exclusive, sterling, and the early-payment discount, as the controller's proposal and
   marked as such. It is fact 5 until John rules it.
10. **PART.** Both are present as slots: the overage rate (fact 3) and the review-call promise
    (fact 7).
11. **DONE.** Licence position (clause 9), the economics disclaimer verbatim from
    `app/aircraft_economics.py` DISCLAIMER_FULL (clause 10), no liability for decisions taken
    on outputs (clause 11), data handling (clause 12).
12. **PART.** Governing law England and Wales is in clause 17. The entity is fact 1 and has no
    default.
13. **PART.** Thirteen lawyer flags carried, each marked in its clause and listed once at the
    foot for the solicitor. Nine slots open in the agreement and seven on the one-pager, all
    listed below. Author metadata and en-GB verified on both Word files by
    `build_w5_docs.py`, which fails the build rather than report a check it did not run.

## Every unfilled slot, and who it waits on

All twelve are John's, by 3 October, so the solicitor has the week of 6 October.

1. **Contracting entity**, registered number and office. Umbrella item 31, no default.
   Agreement SLOT 1, one-pager SLOT G.
2. **Number of launch places**. Agreement SLOT 7, one-pager SLOT B.
3. **Overage rate** for presentations beyond 100. No figure exists anywhere. Until it is set,
   the 100 is a cap. Agreement SLOT 6, one-pager SLOT E.
4. **Internal size thresholds** that place a client in the small, medium or large band. The
   public policy is settled; the thresholds never were. Agreement SLOT 3.
5. **Payment terms**: confirm annual in advance, invoice on signature, 14 days, and set the
   early-payment discount. Agreement SLOT 5, one-pager SLOT F.
6. **Avia's notice period** for ending or suspending the service. Controller's draft is three
   months. Agreement SLOT 9, one-pager SLOT D.
7. **The review call**: one a quarter, with an Avia director. Confirm both. Agreement SLOT 2,
   one-pager SLOT C.
8. **Support**: the address, the person who reads it every working day, the response time.
   Agreement SLOT 8, one-pager SLOT G.
9. **The Meridian route study price**, per route, invoiced on delivery, no licence. Umbrella
   item 35. It leads the one-pager once priced. Agreement SLOT 4, one-pager SLOT A.
10. **The licence record**: dates, participants and what was said on the OAG and Sabre calls.
    Only John and the witnesses hold it.
11. **Invoice detail**: VAT number, bank details, whether a purchase order is required, and
    the numbering. Follows slot 1. Needed for the invoice template.
12. **The solicitor**, and the slot in the week of 6 October.

## Judgement calls W5 made, for the controller to overturn if wrong

1. **The illustrative list is printed to the nearest pound** (£15,914, £21,218, £26,523 in
   year 3), not the nearest £50. A buyer with a calculator who takes 85% of a rounded list
   arrives £50 below the printed cash price, and that argument is not worth having in a
   meeting. The launch figures themselves follow the ruling exactly: nearest £50.
2. **The one-pager runs to two pages**, printed double-sided. The price table, the three-year
   schedule, the four conditions and the exit terms do not fit on one side at a size anyone
   will read across a table.
3. **The agreement is 17 clauses and 4 pages** with the markers in. The ruling of 19 September
   said two pages; the rulings of 20 September added escalation, renewal, add-ons, new
   functions and Avia's exit. Two pages is no longer achievable honestly.

## Watchpoints

1. **The step from year 3 to year 4** is from 85% of list to list, and the client meets it in
   the same year that escalation starts applying to it. The schedule is on the one-pager and
   in the agreement from the first meeting, which is what John asked for, but the renewal
   conversation in year 4 is the one that decides whether a launch client stays.
2. **Clause 9 remains the exposure.** Avia sells outputs from data licensed from OAG and
   Sabre on verbal permission. Clause 15 now carries the consequence of a provider
   restricting sharing, which is the right place for it, but the letters are still the answer.
3. **The accuracy line and umbrella item 25.** Clause 10 states the ruled sentence and nothing
   beyond it. If item 25 rules (a), the clause stands as drafted.
4. **Prices are in a printed document before they are on the website.** The one-pager is the
   first written price a prospect sees, which the ruling intends. It is also the version a
   prospect will hold in November when the website publishes; the two must agree.

## Conflicts seen

None outstanding. Both conflicts raised in v2 are fixed in the umbrella: the W5 row is
rewritten and Waiting on John item 20 is cut to one recommendation.

## Commits

`11a4c3f..702d525` carries W5 session 1. This session's files commit against
`COMMIT-MSG-20Sep2026-w5-v02.txt`, per README.md's one message file per commit. The block also
removes the two v0.1 Word files, which the version-free names replace.
