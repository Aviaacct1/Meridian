"""Meridian at Routes World 2026: the ten-slide stand deck, as a renderer-agnostic spec.

W3 scope item 1. The deck the host works from on stand F124 and the five pre-arranged
meetings run on. It is about the product, not about one route: the two worked routes are
evidence, not the subject.

Register: a pitch, not a diligence report. The case is put in the affirmative. Nothing
about any competitor appears, here or anywhere else (commercial plan, section 10).

Build state, 21 September 2026. Slides 1-6 and 9-10 carry their final structure with the
four messaging sentences as PLACEHOLDERS, taken verbatim from
ROUTES-CONTROLLER-QUEUE-19Sep2026.md section B, to be swapped when John and Jol settle
them on 25 September. Slides 7 and 8 are held for two real runs; the carrier for
Bologna-New York is with John (umbrella item 26) and the controller has ruled the runs
come off the frozen build.

Run: python3 render_pptx.py spec_routes_stand -o Meridian_Routes_Stand_Deck.pptx

Avia Solutions Limited. All rights reserved.
"""

import deck_spec as S

CODENAME = "Meridian"

# Every figure carries a source in the same place. These are the three the deck uses.
SRC_PRICING = ("Source: Meridian pricing and the commercial offer, "
               "PRICING-DECISION-2026.md v1.0, FINAL, 20 September 2026.")
SRC_METHOD = ("Source: Meridian forecasting methodology, The Aviation Observatory, "
              "23 August 2026.")
SRC_CALIB = ("Source: Meridian calibration record, 6,524 real route launches, "
             "2016-2019, 2024 and 2025; the pandemic years 2020-2023 are excluded. Outturn is "
             "Sabre Global Demand Data throughout; calibration rule B, 26 September 2026.")

# --- PLACEHOLDERS, swapped on 25 September ---------------------------------
# Verbatim from ROUTES-CONTROLLER-QUEUE-19Sep2026.md section B, marked DRAFT there.
P_ONELINER = ("Run your route forecast on our stand, in seconds: 25 years of QSI "
              "practice, built into a tool and calibrated against real route launches.")
P_SUB_1 = "The best time of day to fly it, not just how many will fly it."
# "the same day", not a minutes figure: controller ruling of 19 September, carried in
# PRICING-DECISION-2026.md v1.0 section 7. The minutes figure returns only after one pack
# has been sent and received over a hotspot at the 11-12 October trial.
P_SUB_2 = "A researched pack with your numbers, emailed the same day."
P_SUB_3 = "Independent and senior: no network to sell you, no house view."

# The accuracy sentence, John's wording of 25 September and his figures of 26 September
# (umbrella item 55, CLOSED: calibration rule B, Sabre throughout, 6,524 launches). One model,
# one record, one pair; nothing else on the slide states a figure.
ACCURACY = ("When this model was used to forecast the new routes that launched since 2016, "
            "88% of its forecasts were within 20% of what the route went on to carry and "
            "78% within 10%, across 6,524 launches. The past does not predict the future, "
            "but that is the record.")

NOTE_25B = ("If asked what calibrated means: the model is fitted on the full history of "
            "6,524 launches and graded on the same launches. On launches it never saw, a "
            "portfolio of twenty routes lands within 20% of the actual total 94% of the time.")


def build():
    spec = S.deck(
        codename=CODENAME,
        title="Route forecasting, made into a tool",
        strap=P_ONELINER,
        prepared_for="Routes World 2026, Frankfurt",
        event="21-23 October 2026",
        date="October 2026",
        status="DRAFT v0.1. Slides 7 and 8 held for runs off the frozen build",
        confidentiality="Commercial in Confidence",
        author="The Aviation Observatory")

    s = spec["slides"]

    # 1 ---------------------------------------------------------------- cover
    s.append(S.cover(
        ["Meridian", "Route forecasting,", "made into a tool"],
        image="cover.hero", family="globe",
        subtitle="Published by The Aviation Observatory",
        notes="Placeholder one-liner on the cover strap; swap 25 September."))

    # 2 -------------------------------------------------------------- problem
    s.append(S.prose(
        section="The problem",
        title="You are asked to prove a route before anyone will fly it",
        paras=[
            (None,
             "A route development team pitches a route and is asked three questions in "
             "the same meeting: how many passengers, at what load factor, and why the "
             "airline should believe either number. Answering them properly has meant a "
             "consultancy study, six figures of airline planning time, or a spreadsheet "
             "nobody outside the team trusts."),
            (None,
             "The work itself is not the hard part. Measuring the market, scoring the "
             "competing itineraries, adding the connecting feed and fitting the result "
             "to an aircraft is a known method. Doing it in a week, for every route on "
             "the list, and being able to show your working, is the hard part."),
        ],
        # The placeholder runs four characters over the callout budget, so it is set as
        # two lines rather than reworded: a placeholder is quoted, not edited.
        callouts=[S.callout(["Independent and senior:",
                             "no network to sell you, no house view."])],
        notes="Placeholder sub-message in the callout; swap 25 September."))

    # 3 ----------------------------------------------------------- what it does
    s.append(S.grid(
        section="What Meridian does",
        title="Two cities and an airline in, a defended forecast out",
        rows=[
            ("Two cities and an airline",
             "You enter the origin, the destination and the airline you are pitching."),
            ("Airports in play",
             "Every airport travellers in the origin area could use, and every airport "
             "serving the destination city."),
            ("The real market",
             "Passengers who actually flew between those areas, read from booking "
             "data and grown to the forecast year."),
            ("Who uses which airport",
             "Each town allocated by real road driving time, flight quality and airport "
             "size, calibrated against observed origin splits."),
            ("Local demand",
             "The route's share of the local market, from the same choice-of-service "
             "scoring airline network planners use."),
            ("Connecting feed",
             "Passengers connecting behind the origin and beyond the destination, scored "
             "for the named airline and its partnerships."),
            ("Total, aircraft and out",
             "Local plus feed, capped by the aircraft at an achievable load factor, with "
             "the schedule that demand supports."),
        ],
        source=SRC_METHOD,
        notes="Structure from the 2 July methodology deck, slide 2, rewritten to Nick's "
              "note of 23 August. The two July validation figures are out (ruled)."))

    # 4 ------------------------------------------------- three classes of number
    # R1 CARVE-OUT (Jol feedback register, 21 Sep): "measured" becomes "actual" on every
    # client surface EXCEPT this framing and manual section 2, which keep Nick's words
    # until Nick agrees to "actual, calibrated, capped". John is asking him. R2 removes
    # "physics" everywhere else; this slide is inside the same carve-out, so it is left
    # whole rather than half-renamed. Reported to the controller as a tension, not a fix.
    s.append(S.grid(
        section="How to read a forecast",
        title="Every number is one of three kinds",
        rows=[
            ("Measured",
             "Read from data, not assumed: the addressable market, the schedules in the "
             "choice set, the sector distance."),
            ("Calibrated",
             "Fitted to launched-route outcomes: the capture weighting, the coverage "
             "correction, the stimulation uplift, the connecting-feed scoring."),
            ("Physics",
             "A hard constraint: the aircraft and frequency cap, the achievable load "
             "factor, the runway and elevation check."),
        ],
        accent_rows=[1],
        callout=S.callout(["Ask which kind a number is before you argue with it"]),
        source=SRC_METHOD,
        notes="Nick's methodology note, section 2. If a host cannot answer a method "
              "question, the line is: John can take you through it, shall I set that up."))

    # 5 ------------------------------------------------------------- accuracy
    s.append(S.prose(
        section="The calibration record",
        title="We publish our error",
        paras=[(None, ACCURACY),
               (None,
                "The record is out of sample. The model is trained on a set of launch "
                "years and tested only on launches from a year it never trained on, "
                "repeated so every launch is in turn unseen. A portfolio of candidate "
                "routes is measured more accurately than any single one, which is why a "
                "single route is never quoted as a promise.")],
        source=SRC_CALIB,
        notes=NOTE_25B))

    # 6 ------------------------------------------------------ connecting feed
    s.append(S.grid(
        section="The connecting feed",
        title="Who flies it changes the answer",
        rows=[
            ("Behind the origin",
             "Towns feeding in and connecting onto the flight."),
            ("The local market",
             "Point to point between the two cities, the part most models stop at."),
            ("Beyond the destination",
             "Passengers carrying on past the hub to a city the airline serves."),
            ("Why the airline matters",
             "A route into a hub reaches the onward bank only if the carrier or its "
             "partners fly those legs, and only where the connection clears minimum "
             "connecting time and is not a detour. So the forecast is for a named "
             "carrier."),
            ("Why the departure time matters",
             "The departure time decides which onward bank a passenger can legally "
             "reach, so moving the schedule by a short margin moves the feed. That is "
             "what Optimise searches."),
        ],
        accent_rows=[3],
        source=SRC_METHOD,
        notes="Structure from the 2 July deck, slide 3. The 48,115 and the 2.6 times "
              "figures are removed: both predate the 20 August each-way basis fix."))

    # 7, 8 --------------------------------------------- worked routes, held
    s.append(S.figure(
        section="Worked route 1",
        title="San Jose to Taipei, pitched to China Airlines",
        image=None,
        bullets=["Charts held for a run off the frozen build (controller ruling).",
                 "Every passenger figure carries \"each way\" or \"two-way\" in its own "
                 "label, on the chart, never implied by a note (R5 i).",
                 "Every figure carries its source on the slide."],
        notes="HELD. Build after the 10 October freeze so the deck's numbers are the "
              "show's numbers. Layout goes to Jol and Nick on 3 October."))

    s.append(S.figure(
        section="Worked route 2",
        title="Bologna to New York",
        image=None,
        bullets=["Carrier with John, umbrella item 26.",
                 "Same layout as the previous slide, so the two read as one method.",
                 "Charts held for a run off the frozen build."],
        notes="HELD. Bologna chosen over Genoa: registered at the show with three "
              "delegates against two, and a current Meridian tester."))

    # 9 -------------------------------------------------------- product family
    s.append(S.grid(
        section="The product family",
        title="Three tools, three questions",
        rows=[
            ("Meridian",
             "Will this route work, for this airline, on this aircraft, at what time of "
             "day? Forecast, schedule, economics and a researched pack."),
            ("The Observatory Global Forecast",
             "How much traffic will this airport see over the next 25 years, and where "
             "does it come from?"),
            ("The Design Day module",
             "What does that traffic look like on the busiest day, stand by stand and "
             "hour by hour?"),
        ],
        callout=S.callout(["All three published by The Aviation Observatory"]),
        source=SRC_PRICING))

    # 10 ---------------------------------------------------------- the offer
    # PRICING-DECISION-2026.md v1.0 is the only file that states a price, and W3's
    # instruction is one pricing line quoting it, nothing more. The size bands are gone:
    # the axis is airports covered, not airport size. No number of places: John ruled no
    # limit. No airline price anywhere: the Sabre licence does not permit selling to
    # airlines. The wording below is the ruled host sentence, section 7, shortened.
    s.append(S.prose(
        section="Licensing",
        title="Launch clients sign by the end of November",
        paras=[
            (None,
             "Launch clients who sign by 30 November 2026 pay half our list price in year "
             "one, and we hold the year two and year three prices in writing at signature. "
             "For a single airport the list is £15,000 a year, with no limit on users or on "
             "how much you run it. For a group it depends on how many airports you cover "
             "and we quote it."),
            (None,
             "The agreement and onboarding are available immediately after Routes."),
        ],
        # P_SUB_1 runs four over the callout budget, so it is set as two lines rather
        # than reworded: a placeholder is quoted, not edited.
        callouts=[S.callout(["The best time of day to fly it,",
                             "not just how many will fly it."]),
                  S.callout([P_SUB_2])],
        source=SRC_PRICING,
        notes="One pricing line quoting PRICING-DECISION-2026.md v1.0, nothing more "
              "(W3-RULINGS). The host's qualifying question comes first in conversation: "
              "is route development done here, or at group? Placeholder sub-messages in "
              "the callouts swap on 25 September."))

    return spec


if __name__ == "__main__":
    sp = build()
    S.paginate(sp)
    for line in S.check(sp):
        print(line)
    print("%d slides" % len(sp["slides"]))
