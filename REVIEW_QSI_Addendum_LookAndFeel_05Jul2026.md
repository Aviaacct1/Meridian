# Addendum to REVIEW_QSI_for_Opus_05Jul2026 - section 3b: look and feel

(Separate file because the main review was locked open in an editor at write time. Opus: treat
this as section 3b of the review, and amend fix-list item 7 to read: "F1 confidence band on the
result card + F7 tile hierarchy + F9 run stages + F8/F10 tile polish [material / low-medium /
static]".)

Overall verdict from the live screenshots, a delegate's-eye view: the visual design is a
strength, not a gap - clean navy enterprise styling, consistent cards and typography, a
product-family sidebar that sells a roadmap (the SOON badges), sensible defaults, recent-route
chips, progressive disclosure done properly (Expert panel hidden, feed detail only when
relevant), and captions under every number. The findings below are refinements to an already
credible surface.

**F7. Result hierarchy inverts the story.** [material] [cost: low]. The four result tiles carry
equal visual weight and ADDRESSABLE MARKET comes first, so the eye lands on 1,168,675 before
the 47,004 forecast. On a stand, someone will read the big number as the answer. Make TOTAL
FORECAST the dominant tile (size or accent), market as its context, capture share visually
linking the two.

**F8. Zero reads as broken.** [minor] [cost: low]. "CONNECTING FEED 0" as a headline number
looks like an error even with the "point-to-point carrier" caption. When the value is
structurally zero, replace the number with the reason ("none - U2 does not interline"); keep a
number only when it is a real quantity.

**F9. No stage feedback on the main run.** [material for the demo] [cost: low]. The pitch flow
has stage messages; the ten-second main run should too ("measuring the market... scoring
itineraries... fitting the aircraft"). Ten silent seconds on a stand is long, and the stages
are free theatre that also teaches the methodology.

**F10. Highlight the home airport in the catchment bars.** [minor] [cost: low]. "Where the
catchment flies today" renders every airport in the same navy; the origin under assessment
should be the accent colour so the leakage story ("this is what you lose to LGW today") lands
without narration.

**F11. Palette drift between the dashboard and the server-rendered pages.** [minor] [cost:
low]. Track record and Methodology use their own navy/accent constants rather than the
dashboard's CSS tokens; unify so a projector shows one product, not two generations.

**F12. Small-screen behaviour untested.** [material if an iPad features at Routes] [cost:
medium]. The dashboard grid is desktop-first; the server-rendered pages are responsive. If the
stand plan includes handing over an iPad, test at ~1024px and fix the form grid; if demos are
laptop-plus-screen only, deprioritise.

**F13. SOON items are honest but live-looking.** [minor] [cost: low]. The dimmed style is
right; make them visibly non-interactive (no pointer cursor, no dead navigation) so nobody
clicks the roadmap on stage.
