# W6 status: messaging, marketing, website, meetings

W6 writes this file and rewrites it each session; the controller reads it and never edits it.
Version 7, 20 September 2026. Author: Avia Solutions. Session 3.

Read this session: `routes/W6-RULINGS.md` in full, including John's rulings of 20 September
19:30 on the four sentences and on the meetings; `routes/PRICING-DECISION-2026.md` v1.0,
sections 4, 5 and 7. No git command has been run from this chat; every commit is a block John
runs.

## 1. The four sentences, redrafted in the Observatory's voice

`W6-MESSAGING-VARIANTS-19Sep2026.md` is at v3. Version 2's variants are withdrawn.

- **Sentence 1, two versions.** 1-LIVE: "Bring a route to stand F124 and we will build its
  forecast while you wait, in under five minutes", with a longer form that names the
  Observatory as the subject. 1-HELD is the same sentence on "about a minute" and is drafted
  but NOT in use. W6 is not putting the held version in front of John or Jol as a choice while
  it is held: the two are not interchangeable, because one describes the whole demonstration
  and the other describes a single run. The controller releases it on W1 step 2b's
  restart-proof cold numbers, and W6 swaps it in the same day it is released.
- **2.1** is John's wording, adopted as it stands: "The optimal time to fly it, not just how
  many will fly it."
- **2.2** is version B with John's rewording: "You leave with the run you watched, and a full
  presentation pack follows the same day."
- **2.3, the affiliation clause, two versions for John.** A is the controller's draft. B says
  what the affiliate does and carries the independence claim where it belongs, on Avia. W6
  prefers B on the stand and in the invitations and A where one line is all there is, such as
  the exhibitor listing. Neither claims independence for the Observatory in its own right,
  which is what John rejected.
- **Sentence 3** is quoted from `PRICING-DECISION-2026.md` v1.0 section 7 with its version,
  the qualifying question first, and it is not edited in W6's files.
- **Sentence 4** is unchanged and verbatim.

## 2. The five invitations, rewritten

`W6-INVITATIONS-AND-MEETINGS-19Sep2026.md` is at v3. Each invitation now asks the airport to
name one route it wants to learn more about, which the Observatory forecasts ahead of the
meeting. The route W6 had proposed per airport is demoted to an example offered only if they
name none, and Dallas Fort Worth has no example at all, which is no longer a gap because
asking is now the pattern. Each paragraph carries the affiliation clause, the optimal-time
sub-message, "the pack follows the same day", and the launch-terms line closing 30 November.
Dublin and Milan SEA are written as groups.

**The consequence to hold, recorded so nobody is surprised.** A named route now arrives days
before the meeting, so the pre-run cannot wait on a person: W1's pre-warm covers the five
airports, and whoever takes the reply must forward the route to the stand build the same day.
That handover is not written down anywhere yet. If a route lands inside 48 hours it runs live
in the meeting instead, which the tool can do.

## 3. Marketing calendar

`W6-MARKETING-CALENDAR-19Sep2026.md` is at v3. Post 1 is rebuilt on the ruled sentences: the
Observatory's voice, "under five minutes", the affiliation clause, the optimal-time line, the
same-day pack and the accuracy line verbatim. The list email carries the same claim. Both are
ready for John's approval with nothing waiting on them.

## 4. Conflicts seen

1. **The live site now contradicts the pricing decision.** Commit `6d153d2` on
   `Aviaacct1/tao-website` says "three seats" and "100 presentations included" on the pricing
   page, the Meridian page, the Global Forecast page and in `src/_data/site.json`. That was the
   licence shape in `PRICING-HANDOVER-19Sep2026.md`. `PRICING-DECISION-2026.md` v1.0 section 7
   replaces it with "no limit on users or on how much you run it". The site is not public, so
   nothing is wrong in front of a buyer, but the copy is wrong and W6 will not leave it: the
   fix is a pass over those four files, and W6 will make it in the next session unless the
   controller wants it sooner.
2. **"Limited places" survives in one sentence that no longer has any.** Section 4 of the
   pricing decision rules NO limit on launch places, the 30 November date being the only
   limit. Section 7's fallback sentence, if John holds the silence rule to 3 October, still
   says "on request, limited places". W6 quotes section 7 as it stands rather than editing it,
   and flags the line for W8: it is a published untruth sitting next to a published error
   record, which is the argument section 4 itself makes.
3. **The earlier year-1 figures in W6's own files were wrong and are corrected.** The
   invitations file carried £7,500, £10,000 and £12,500 by airport size. The bands are by
   airports covered, and the year-1 cash is £7,500, £11,250 and £15,000. No document outside
   W6 had taken the wrong figures.

## 5. Website: where it stands

Removals landed at `6d153d2`, pushed. The clean-clone proof is still owed and is the block
John has not run; it clones what is on GitHub, builds it, and counts the competitor's name and
the price figures in the built output, both of which must be zero. The Pages project waits on
W2 moving the zone in the week of 22 September. Item 1 above is now queued in front of the
Pages work, because the wrong licence shape should not be what goes live.

## 6. What W6 needs from John

1. **One contact name per airport**, by 25 September. The invitations are otherwise finished
   and the 26 to 29 September window is the date that cannot be recovered.
2. **Sentence 2.3: version A or version B.**
3. **Approval of post 1 and the contact-list email**, which have nothing else waiting on them.
4. Nothing on pricing. Section 4 of the pricing decision closed item 6 in full: 50%, no limit
   on places, 30 November 2026.

## 7. Risks W6 is carrying

1. The reply-to-forecast handover for a named route has no owner and no written step. It is
   small, and it is the kind of small thing that fails in a week when everyone is travelling.
2. The Pages project cannot start until the zone moves, and the site carries a licence shape
   the pricing decision has superseded.
3. Five invitations go out naming example routes not yet checked against OAG. The check is now
   four routes rather than five, and it happens before sending.
