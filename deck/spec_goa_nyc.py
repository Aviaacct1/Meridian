"""Project Liguria: Genoa to New York. The deck content, as a renderer-agnostic spec.

Client-facing register: this is a pitch, not a diligence report. The case is put
in the affirmative throughout. Objections are answered where they are answered at
all, never raised unprompted. The risk register, the failed comparables and the
open data gaps live in the internal annex, which the airport keeps and the airline
never sees.

Avia Solutions Limited. All rights reserved.
"""

import deck_spec as S

CODENAME = "Project Liguria"
BASIS = ("Source: AviaSolutions analysis, Genoa - New York business case, central "
         "planning case. Route economics in US dollars; Italian traffic and economic "
         "figures in euro or as published.")

CASE = {
    "freq": 7, "lf_cap": 0.85, "seats_y": 162, "seats_j": 20,
    "natural_catchment": 138608, "carried_today": 9043, "annual_pax": 112622,
    "rev": [("Economy", 95013), ("Business", 47600), ("Cargo", 7260)],
    "net_rev": 149873, "charges_recovery": 14341, "gross_rev": 164214,
    "var": [("Fuel", 40500), ("Maintenance", 14740), ("Catering", 819),
            ("Landing", 4429), ("Passenger airport charges", 15934),
            ("En-route navigation", 1135), ("Ground handling", 5871)],
    "fixed": [("Ownership", 16881), ("Insurance", 2157), ("Crew", 21600)],
    "indirect": [("Admin, 5% of net revenue", 7494), ("Sales, 5% of net revenue", 7494)],
    "var_total": 83429, "fixed_total": 40637, "indirect_total": 14987,
    "total_cost": 139053, "profit_turn": 25160, "margin": 0.153,
    "breakeven_lf": 0.689, "annual_profit": 9158339, "standalone_profit": 5127639,
    "block_hours": 6552, "aircraft": 2, "util_vs_full": 0.604, "spare_bh": 4298,
    "own_charged": 6144508, "own_dedicated": 10175208,
    "season_idx": [0.527, 0.448, 0.701, 1.173, 1.128, 1.264, 1.381, 1.637,
                   1.260, 1.047, 0.689, 0.747],
    "season_a": 9183500, "season_b": 7759505, "season_c": 8868071,
    "fuel_grid": [0.68, 0.80, 0.90, 1.00, 1.10],
    "profit_grid": [12.8, 10.8, 9.2, 7.5, 5.9],
    "network": [("GOA-JFK", "120 turns/yr", 33446, 18018925, 15147434, 2871491, 0.159, 0.398),
                ("GOA-EWR", "90 turns/yr", 25085, 13517928, 11306384, 2211544, 0.164, 0.301),
                ("GOA-BOS", "60 turns/yr", 16723, 9003240, 7329369, 1673871, 0.186, 0.198)],
    "network_total": (75254, 40540093, 33783186, 6756907, 0.167, 0.897),
}


def f(n, dp=0):
    return "{:,.{}f}".format(n, dp)


def p(x, dp=1):
    return "{:.{}f}%".format(x * 100, dp)


def build():
    d = S.deck(CODENAME, "A direct link between Genoa and New York",
               "Daily Airbus A321XLR, Genoa Cristoforo Colombo to New York",
               "Aeroporto di Genova and Regione Liguria",
               "World Routes 2026", "5 August 2026", status="DRAFT",
               currency_note="Route economics in US dollars; Italian figures in euro or as published")
    add = d["slides"].append

    # 1 cover
    add(S.cover(["A direct link between", "Genoa and New York"],
                image="cover.hero", family="globe"))

    # 2 contents
    add(S.contents([("1", "The opportunity in one slide", 0),
                    ("2", "Genoa and its catchment", 0),
                    ("3", "The Genoa - New York corridor", 0),
                    ("4", "The Italian secondary-airport wave", 0),
                    ("5", "Route economics", 0),
                    ("6", "Methodology and track record", 0),
                    ("7", "The airport, the aircraft and the ask", 0),
                    ("8", "Appendix", 0)],
                   title="Contents",
                   subtitle="A direct link between Genoa and New York"))

    # 3 the case
    add(S.grid(
        section="Section 1 - The opportunity in one slide",
        title="The case for Genoa",
        subtitle="Six reasons, each evidenced in the sections that follow",
        rows=[
            ("An existing corridor, in freight",
             "Circa 37% of Genoa and Savona port traffic is United States linked, circa 336,000 container units a year, and MSC runs a direct nine-day Genoa to New York container service. The commercial corridor already exists."),
            ("The fastest-growing of the three",
             "Genoa grew 18.1% to 1,587,761 passengers in 2025, against Malpensa's 8.6% and Fiumicino's 4.5%, on the regulator's own comparable table."),
            ("A gateway already moving visitors at scale",
             "1,630,593 cruise passengers used Genoa in 2025, more than the airport itself handled, and the cruise sector is worth EUR 346m to the Genoa and Savona economy."),
            ("The aircraft now reaches",
             "Genoa to New York is 3,509.6 nautical miles, circa 75% of the A321XLR's published 4,700 nm range, and shorter than Madrid to Boston, which has operated since 14 November 2024."),
            ("A base, not a single route",
             "Three United States points from one Genoa base fill 0.90 of a frame in a single summer programme, at a %s network margin on $%.1fm of revenue." % (
                 p(CASE["network_total"][4], 1), CASE["network_total"][1] / 1e6)),
            ("Nobody else has moved",
             "Genoa is the largest north-western Italian catchment with no United States service, in a year when five other secondary Italian airports gained one."),
        ],
        accent_rows=[0, 4],
        callout=S.callout(["A %s route margin at a %s breakeven load factor" % (
            p(CASE["margin"], 1), p(CASE["breakeven_lf"], 1))]),
        source="Sources: Autorita di Sistema Portuale del Mar Ligure Occidentale via Genova24, October 2024; ENAC Air Traffic Data 2025, January 2026; Stazioni Marittime SpA via ANSA, 13 January 2026; Airbus published range; AviaSolutions analysis."))

    # 4 summary
    add(S.stat_row(
        section="Section 1 - The opportunity in one slide",
        title="Summary of the proposition",
        subtitle="Daily Airbus A321XLR, Genoa to New York, central planning case",
        figure="goa_map_route.png",
        stats=[("Genoa natural New York catchment", f(CASE["natural_catchment"]), False),
               ("Carried through Genoa today", f(CASE["carried_today"]), False),
               ("Forecast passengers, year 1", f(CASE["annual_pax"]), True)],
        table={"head": ["Sector", "Aircraft", "Op. days", "Total seats",
                        "Weekly freq.", "Business", "Economy", "Annual pax yr 1",
                        "Planning LF"],
               "rows": [["GOA-JFK", "A321XLR", "Daily", "182", str(CASE["freq"]),
                         f(CASE["seats_j"]), f(CASE["seats_y"]),
                         f(CASE["annual_pax"]), p(CASE["lf_cap"], 0)]],
               "widths": [1.0, 1.0, 0.85, 0.9, 0.95, 0.85, 0.85, 1.1, 0.95]},
        callouts=[S.callout(["Route margin %s, breakeven load factor %s" % (
                      p(CASE["margin"], 1), p(CASE["breakeven_lf"], 1))]),
                  S.callout(["Annual profit $%.1fm on the network basis" % (
                      CASE["annual_profit"] / 1e6)], tone="dark")],
        source=BASIS + " Catchment demand from AviaSolutions catchment allocation on GeoNames population and OSRM road times; New York market split and fares from Sabre ODPOO 2024. Distance 3,509.6 nm."))

    # ---------------------------------------------------------------- 2
    add(S.divider("2", "Genoa and its catchment",
                  "The airport, the region and the demand that departs from somewhere else today",
                  image="divider.catchment", family="field"))

    add(S.keynumbers(
        section="Section 2 - Genoa and its catchment",
        title="Genoa in six numbers",
        subtitle="The regulator's own figures",
        items=[("1.59m", "Passengers in 2025, up 18.1%, the fastest growth of Italy's three north-western gateways"),
               ("19th", "Rank among the 44 Italian airports open to commercial traffic"),
               ("1.63m", "Cruise passengers through Genoa in 2025, more than the airport itself handled"),
               ("37%", "Share of Genoa and Savona port traffic that is United States linked"),
               ("20.3m", "People in the four regions from which Genoa can draw, on ISTAT counts"),
               ("Zero", "Long-haul services at Genoa today, in the largest unserved catchment in the north west")],
        source="Sources: ENAC, Air Traffic Data 2025 - Executive Summary, Airport Traffic Table, published January 2026; Stazioni Marittime SpA reported by ANSA, 13 January 2026; Autorita di Sistema Portuale via Genova24, October 2024; ISTAT and Regione Emilia-Romagna, reference dates 2023 to 2026, four-region total is an AviaSolutions calculation."))

    add(S.figure(
        section="Section 2 - Genoa and its catchment",
        title="Genoa is growing faster than Milan or Rome",
        subtitle="The regulator's comparable table, all 44 Italian airports on one basis",
        image="goa_ch_traffic.png",
        table={"head": ["Airport", "2025 growth", "National rank"],
               "rows": [["Genoa", "+18.1%", "19th"],
                        ["Milan Malpensa", "+8.6%", "2nd"],
                        ["Rome Fiumicino", "+4.5%", "1st"]],
               "widths": [1.4, 0.9, 0.9]},
        panels=[S.panel("What is behind it", [
            "Ten new routes and 1,375,000 summer 2026 seats, up 10% on summer 2025.",
            "Genoa exceeded its 2019 peak in 2025 and reported an all-time record.",
            "The first four months of 2026 ran 17.9% ahead of the same period in 2025.",
        ])],
        source="Sources: ENAC, Air Traffic Data 2025 - Executive Summary, Airport Traffic Table, published January 2026; GuidaViaggi reporting the airport operator, 19 March 2026 and 7 May 2026."))

    add(S.figure(
        section="Section 2 - Genoa and its catchment",
        title="The catchment, and who serves it today",
        subtitle="Six airports between one and two and a half hours away, none of them in Liguria",
        image="goa_map_catchment.png",
        table={"head": ["Airport", "Road", "Drive", "Rail"],
               "rows": [["Milan Malpensa", "180-188 km", "1h58-2h06", "circa 2h20-2h35, two legs"],
                        ["Milan Linate", "circa 151 km", "1h43", "circa 2h00-2h30, two legs"],
                        ["Milan Bergamo", "190-191 km", "2h07-2h22", "combination"],
                        ["Turin city", "171 km", "1h53", "1h41-1h49 direct"],
                        ["Nice", "195-200 km", "2h22", "circa 3h, 3 direct trains"],
                        ["Pisa", "158-176 km", "1h50-2h09", "circa 2h09"]],
               "widths": [1.25, 0.95, 0.85, 1.61]},
        panels=[S.panel("The regulator's own classification", [
                    "The Piano Nazionale degli Aeroporti 2026-2035 places Genoa in the same Nord-Ovest traffic basin as Malpensa, Linate, Bergamo, Turin and Cuneo.",
                ]),
                S.panel("Terzo Valico", [
                    "The Genoa to Milan high-speed link, targeted at circa 1h07 from 2027, makes Genoa a viable origin airport for Lombard passengers for the first time.",
                ], tone="accent")],
        source="Sources: Ministero delle Infrastrutture e dei Trasporti, Piano Nazionale degli Aeroporti 2026-2035, 15 July 2026; drive and rail times from routing and ticketing aggregators, retrieved 5 August 2026, estimates; Terzo Valico timing per RFI reported by TrasportoEuropa, July 2026, a forecast."))

    add(S.prose(
        section="Section 2 - Genoa and its catchment",
        title="Ligurian transatlantic demand flies from elsewhere",
        subtitle="Genoa has no United States service, so the demand is being carried by six other airports",
        paras=[("The structural position",
                "Genoa is the only one of Italy's three north-western gateways with no United States service and, in summer 2026, no route "
                "extending beyond the European periphery. Every resident of Liguria travelling to the United States today therefore begins "
                "that journey at Malpensa, Linate, Bergamo, Turin, Nice or Pisa, or connects over a European hub."),
               ("What the national regulator says",
                "The Piano Nazionale degli Aeroporti 2026-2035 places Genoa in the same Nord-Ovest traffic basin as Malpensa, Linate, Bergamo, "
                "Turin and Cuneo. The demand is formally recognised as shared; the service is not."),
               ("Sizing it precisely is a fortnight of work",
                "A Sabre origin-destination pull keyed to Ligurian and western Lombard postcodes converts the structural argument into a measured "
                "one, airport by airport and carrier by carrier. It is the first thing an airline will ask for and Avia can deliver it before "
                "the carrier conversation rather than after."),
               ("What the forecast in section 5 uses",
                "The modelled catchment allocation, built at cell level from population, employment and road times, not the four-region total. "
                "The four-region figure describes the region Genoa draws from; the forecast uses only demand allocated to Genoa itself.")],
        panels=[S.panel("The four-region population", [
                    "Liguria 1.51m, Piemonte 4.25m, Lombardia 10.03m, Emilia-Romagna 4.49m: circa 20.3m.",
                    "A four-region total, not a drive-time isochrone, and labelled as one throughout.",
                ]),
                S.panel("Genoa's own natural share", [
                    "The catchment model puts Genoa's natural New York market at %s passengers a year." % f(CASE["natural_catchment"]),
                    "Genoa carries %s of them today." % f(CASE["carried_today"]),
                ], tone="accent")],
        source="Sources: ISTAT via tuttitalia.it and Regione Emilia-Romagna Servizio Statistica for population, reference dates 31 December 2023 to 1 January 2026; four-region total is an AviaSolutions calculation; Ministero delle Infrastrutture e dei Trasporti, Piano Nazionale degli Aeroporti 2026-2035, 15 July 2026."))

    # ---------------------------------------------------------------- 3
    add(S.divider("3", "The Genoa - New York corridor",
                  "Freight, cruise, diaspora and corporate links that already run between the two cities",
                  image="divider.corridor", family="field"))

    add(S.table(
        section="Section 3 - The Genoa - New York corridor",
        title="The corridor already exists, in freight",
        subtitle="A quantified Genoa to New York commercial relationship with no air link",
        table={"head": ["Measure", "Figure", "Source"],
               "rows": [["Genoa and Savona port traffic that is United States linked", "circa 37%", "Autorita di Sistema Portuale, October 2024"],
                        ["Container units a year on that United States trade", "circa 336,000", "As above"],
                        ["MSC Genoa to New York container service", "Direct, nine-day transit", "TrasportoEuropa, MEDUSEC service"],
                        ["Genoa cruise passengers, 2025", "1,630,593", "Stazioni Marittime SpA via ANSA, 13 January 2026"],
                        ["Cruise value to the Genoa and Savona economy", "EUR 346m", "MedCruise and Ports of Genoa impact study"],
                        ["ERG, Genoa headquartered, United States acquisition", "USD 270m for 75% of a 317 MW platform", "ERG press release, 21 December 2023"]],
               "widths": [3.9, 2.2, 3.3]},
        callouts=[S.callout(["The freight corridor is direct and scheduled.",
                             "The passenger corridor is not."])],
        bullets=[("The Austrian Airlines proof point.",
                  "Austrian flies a dedicated weekly Vienna to Genoa charter from 2 May to 31 October 2026 purely to feed the Costa cruise terminal. That is the demand mechanism this route depends on, already operating at short-haul scale.")],
        source="Sources as shown in the table; Austrian Airlines charter per GenovaToday, retrieved 5 August 2026."))

    add(S.table(
        section="Section 3 - The Genoa - New York corridor",
        title="The New York end of the demand",
        subtitle="A large Italian-American base at the United States end of the route",
        table={"head": ["Measure", "Figure", "Source"],
               "rows": [["Italian ancestry, New York State and New Jersey", "circa 3.44m", "US Census ACS 2020-2024, table B04006"],
                        ["New York JFK", "Level 3 slot controlled", "IATA designation"],
                        ["Newark", "United's hub; every recent secondary Italian route", "Carrier route announcements 2022-2026"],
                        ["Distance, Genoa to New York", "3,509.6 nm, circa 75% of A321XLR range", "Airbus published range"]],
               "widths": [2.6, 2.2, 2.6]},
        panels=[S.panel("Why visiting friends and relatives matters here", [
                    "It books early, travels in the shoulder months and is far less fare-elastic than leisure.",
                    "It is the ballast under a thin long-haul route, and it is the flow that fills January and February.",
                ]),
                S.panel("Our view on the operator", [
                    "United is the closest fit on evidence: it holds Newark, it has taken Palermo, Bari and Olbia, and it backfilled a route another operator left.",
                    "La Compagnie is the interesting second, on the strength of four years of Newark to Malpensa on an all-business A321neo.",
                ], tone="accent")],
        source="Source: US Census American Community Survey 2020-2024 5-year estimates, table B04006, to be verified on data.census.gov before issue; carrier route announcements 2022-2026; Airbus published range. AviaSolutions analysis."))

    # ---------------------------------------------------------------- 4
    add(S.divider("4", "The Italian secondary-airport wave",
                  "What has launched since 2022, and why Genoa is the one that has not",
                  image="divider.wave", family="operations"))

    add(S.table(
        section="Section 4 - The Italian secondary-airport wave",
        title="Secondary Italian airports now carry United States service",
        subtitle="Four carriers, seven or more nonstops, from catchments smaller than Genoa's",
        table={"head": ["Italian airport", "Carrier", "United States point", "Status"],
               "rows": [["Naples", "American, United, Delta", "Philadelphia, Newark, New York JFK", "Operating"],
                        ["Catania", "Delta, Neos", "New York JFK", "Operating"],
                        ["Palermo", "United", "Newark", "Circa 85% load factor, extended to December 2026"],
                        ["Bari", "United", "Newark", "Operating"],
                        ["Olbia", "United", "Newark", "Operating"],
                        ["Milan Malpensa", "La Compagnie", "Newark, all-business A321neo", "5x weekly since 15 April 2022"],
                        ["Genoa", "None", "None", "The largest north-western catchment with no service"]],
               "widths": [1.5, 2.2, 3.0, 3.1]},
        callouts=[S.callout(["La Compagnie has flown a narrowbody, premium-",
                             "configured northern Italy to New York route",
                             "for four years"]),
                  S.callout(["United's Newark to Palermo runs at circa 85%",
                             "load factor and has been extended into",
                             "December 2026"], tone="dark")],
        source="Sources: carrier route announcements and Italian and United States aviation trade press, retrieved 5 August 2026; Palermo load factor per Travel And Tour World and Dream of Italy, January 2026. To be replaced with an OAG schedule extract before issue."))

    add(S.prose(
        section="Section 4 - The Italian secondary-airport wave",
        title="Why Genoa is next, and why this is not Gothenburg",
        subtitle="The four things that separate this proposition from the thin narrowbody routes that did not hold",
        paras=[("A base, not a single rotation",
                "The routes that have struggled shared a shape: one secondary origin, one United States point, one narrowbody, and nowhere to move "
                "the aircraft when the first market softened. Genoa is put forward as three United States points from one base, filling 0.90 of a "
                "frame in a single summer programme. That gives an operator somewhere to go."),
               ("A catchment with a second gateway already at scale",
                "Genoa handles more cruise passengers than air passengers. 1,630,593 people already arrive and depart internationally through the "
                "city by another mode, and Austrian already flies a dedicated charter to feed them. Few secondary airports have a demand engine "
                "of that size sitting next to the runway."),
               ("A corridor that exists in freight before it exists in air",
                "Circa 37% of the port's traffic is United States linked and MSC sails Genoa to New York direct. The commercial relationship is "
                "established; the passenger link is the missing piece, not a speculative one."),
               ("A share argument, and share goes to whoever moves first",
                "Five secondary Italian airports gained United States service in four years. Genoa is the largest north-western catchment still "
                "without one, and no operator has announced a plan. The window is open now and it will close behind whoever takes it.")],
        callouts=[S.callout(["Three points from one base, at %s network margin" % p(CASE["network_total"][4], 1)])],
        source="Sources: AviaSolutions network model; Stazioni Marittime SpA via ANSA, 13 January 2026; Autorita di Sistema Portuale via Genova24, October 2024; carrier route announcements 2022-2026."))

    # ---------------------------------------------------------------- 5
    add(S.divider("5", "Route economics",
                  "The route profit and loss, the fleet question, seasonality and the sensitivities",
                  image="divider.economics", family="instruments"))

    rev_rows = [[k, "$%s" % f(v)] for k, v in CASE["rev"]]
    rev_rows += [["Net revenue", "$%s" % f(CASE["net_rev"])],
                 ["Charges recovery", "$%s" % f(CASE["charges_recovery"])],
                 ["Gross revenue", "$%s" % f(CASE["gross_rev"])]]
    cost_rows = [[n, "$%s" % f(v)] for n, v in CASE["var"]]
    cost_rows.append(["Variable cost", "$%s" % f(CASE["var_total"])])
    cost_rows += [[n, "$%s" % f(v)] for n, v in CASE["fixed"]]
    cost_rows.append(["Direct fixed", "$%s" % f(CASE["fixed_total"])])
    cost_rows.append(["Indirect fixed, admin and sales", "$%s" % f(CASE["indirect_total"])])
    cost_rows.append(["Total cost", "$%s" % f(CASE["total_cost"])])
    add(S.table(
        section="Section 5 - Route economics",
        title="Route profit and loss per turnaround",
        subtitle="Central planning case, US dollars per return rotation, daily A321XLR",
        table={"head": ["Revenue", "Per turnaround"], "rows": rev_rows,
               "widths": [2.9, 1.56], "total": True},
        table2={"head": ["Cost", "Per turnaround"], "rows": cost_rows,
                "widths": [2.9, 1.56], "total": True},
        callouts=[S.callout(["Profit per turnaround", "$%s" % f(CASE["profit_turn"])]),
                  S.callout(["Route margin", p(CASE["margin"], 1)], tone="dark"),
                  S.callout(["Breakeven load factor", p(CASE["breakeven_lf"], 1)])],
        source=BASIS + " Maintenance from the validated Airbus 2024-2025 reserves; ownership from appraiser lease rates; fuel at $0.90 per kilogramme through-cycle."))

    add(S.figure(
        section="Section 5 - Route economics",
        title="The result, and the fleet decision behind it",
        subtitle="The headline assumes the aircraft is productive when it is not flying to New York",
        image="goa_ch_cost.png",
        table={"head": ["Measure", "Value"],
               "rows": [["Network basis, fleet kept busy", "$%.2fm" % (CASE["annual_profit"] / 1e6)],
                        ["Standalone, Genoa-only fleet", "$%.2fm" % (CASE["standalone_profit"] / 1e6)],
                        ["Ownership charged in the headline", "$%.2fm" % (CASE["own_charged"] / 1e6)],
                        ["True ownership if dedicated", "$%.2fm" % (CASE["own_dedicated"] / 1e6)],
                        ["Annual block hours flown", f(CASE["block_hours"])],
                        ["Utilisation against a full year", p(CASE["util_vs_full"], 1)],
                        ["Spare block hours a year", f(CASE["spare_bh"])]],
               "widths": [2.35, 1.05]},
        bullets=[("The route is profitable either way.",
                  "$%.1fm a year on the network basis and $%.1fm standalone. The gap is ownership recovery, and it is why the three-point base in the next slide is the shape we recommend." % (
                      CASE["annual_profit"] / 1e6, CASE["standalone_profit"] / 1e6)),
                 ("The spare capacity is an opportunity, not a cost.",
                  "%s spare block hours a year is a second and third market, which is exactly what the Genoa base programme uses them for." % f(CASE["spare_bh"]))],
        source=BASIS))

    net_rows = []
    for name, prog, pax, rev, cost, prof, marg, frames in CASE["network"]:
        net_rows.append([name, "A321XLR", prog, f(pax), "$%s" % f(rev),
                         "$%s" % f(cost), "$%s" % f(prof), p(marg, 1), "%.2f" % frames])
    t = CASE["network_total"]
    net_rows.append(["Network total", "", "", f(t[0]), "$%s" % f(t[1]),
                     "$%s" % f(t[2]), "$%s" % f(t[3]), p(t[4], 1), "%.2f" % t[5]])
    add(S.table(
        section="Section 5 - Route economics",
        title="Three United States points from one Genoa base",
        subtitle="The same aircraft, three markets, one summer programme",
        table={"head": ["Route", "Aircraft", "Programme", "Annual pax",
                        "Annual revenue", "Annual cost", "Annual profit",
                        "Margin", "Frames"],
               "rows": net_rows,
               "widths": [1.0, 0.8, 1.05, 0.95, 1.25, 1.25, 1.25, 0.65, 0.65],
               "total": True},
        callouts=[S.callout(["One aircraft covers the whole",
                             "summer programme, at 0.90 frames"]),
                  S.callout(["Network margin %s on" % p(t[4], 1),
                             "$%.1fm of annual revenue" % (t[1] / 1e6)], tone="dark")],
        bullets=[("This is a base decision, not a route decision.",
                  "Genoa to New York alone does not fill an aircraft. Genoa to New York, Newark and Boston does, inside one summer programme. That is a different and much easier conversation with an airline."),
                 ("What it asks of the airport.",
                  "Overnight parking, crew facilities and a ground handling arrangement carrying three United States rotations a week at the summer peak. Those are airport commitments, and they are in the offer.")],
        source=BASIS + " Network programme from the Genoa base summer schedule model."))

    add(S.figure(
        section="Section 5 - Route economics",
        title="Seasonality is an operating choice, not an obstacle",
        subtitle="Genoa's June to September concentration is identical to the Italian national figure",
        image="goa_ch_season.png",
        table={"head": ["Operating pattern", "Annual profit"],
               "rows": [["Nominal flat, planning load factor every month", "$%.2fm" % (CASE["season_a"] / 1e6)],
                        ["Flat daily schedule, real monthly demand", "$%.2fm" % (CASE["season_b"] / 1e6)],
                        ["Seasonal schedule, winter trimmed", "$%.2fm" % (CASE["season_c"] / 1e6)]],
               "widths": [2.35, 1.05]},
        panels=[S.panel("Genoa is normal for Italy", [
                    "June to September is circa 41% of Genoa's annual traffic, the same as the 41% national figure.",
                ]),
                S.panel("The operating answer", [
                    "Trimming January, February, November and December recovers $1.11m against a flat winter schedule.",
                    "The airport should price both a year-round and a seasonal package so the carrier can choose.",
                ], tone="accent")],
        source="Sources: monthly demand index is an AviaSolutions working assumption pending a monthly Sabre pull; Genoa's June to September concentration derived from operator monthly data with December verified against Assaeroporti; national figure from ENAC, January 2026."))

    add(S.figure(
        section="Section 5 - Route economics",
        title="The route holds across the tested range",
        subtitle="Profitable from $0.68 to $1.10 per kilogramme, and demand is not the constraint",
        image="goa_ch_fuel.png",
        panels=[S.panel("Fuel is the live variable", [
                    "A move from $0.68 to $1.10 per kilogramme takes annual profit from $12.8m to $5.9m.",
                    "The route stays profitable across the whole tested band.",
                ]),
                S.panel("Demand is not the constraint", [
                    "Across a capture range of 50% to 75% of catchment demand, annual profit does not change: the planning load-factor cap binds throughout.",
                    "In plain terms, seats are the constraint, not passengers. The commercial risk sits in cost, not in whether the catchment shows up.",
                ], tone="accent")],
        source=BASIS + " Scenario grid from the business case; capture defined as the share of catchment demand recovered by a Genoa service."))

    # ---------------------------------------------------------------- 6
    add(S.divider("6", "Methodology and track record",
                  "How the case is built, and how the engine behind it has been tested",
                  image="divider.methodology", family="instruments"))

    add(S.prose(
        section="Section 6 - Methodology and track record",
        title="Basis of the case",
        subtitle="What is modelled, what is assumed, and where each input comes from",
        paras=[("Catchment and demand",
                "Catchment allocation from GeoNames population and OSRM road times, validated. The New York origin and destination market split "
                "and the fares come from Sabre ODPOO 2024, validated. Fares are one-way, economy $345 and business $1,400, an entrant-yield "
                "judgement rather than an observed Genoa fare."),
               ("Economics",
                "The cost stack is anchored to the Avia route economics module. Maintenance comes from the validated Airbus 2024-2025 reserves. "
                "Ownership comes from appraiser lease rates. Fuel at $0.90 per kilogramme is a through-cycle planning assumption, tested from "
                "$0.68 to $1.10."),
               ("Every figure carries its source",
                "Each slide in this deck carries a named publisher and a date in the same line as the figure. Where an input is a judgement or a "
                "working assumption it is described as one, in the assumptions register in the appendix."),
               ("The forecast engine",
                "Passenger forecasts come from the Avia Cortex QSI engine: base demand grown to maturity, service-area demand only, stimulated "
                "for new direct service, and captured from frequency share, schedule quality and observed leakage rather than assumed.")],
        source="Source: AviaSolutions assumptions register, Genoa - New York business case, version of 5 August 2026."))

    add(S.figure(
        section="Section 6 - Methodology and track record",
        title="Tested against 2,915 real route launches",
        subtitle="The engine behind this forecast, graded against what actually flew",
        image="QSI_accuracy_distribution_fitted.png",
        panels=[S.panel("How the test was built", [
                    "Every genuinely new route launched worldwide in 2016-2019 and 2025, 2,915 of them, from the complete OAG schedule archive.",
                    "For each one the engine saw only the world as it stood the month before launch.",
                    "Its first-year forecast was then compared with the passengers who actually flew.",
                ]),
                S.panel("And on routes never seen", [
                    "Forecasting portfolios of twenty unseen routes, the portfolio total came within 20% of the actual total 94% of the time.",
                ], tone="accent")],
        callouts=[S.callout(["89% within 20% of outturn", "82% within 10%"])],
        source="Source: Avia Cortex QSI backtest programme, runs of 5 August 2026, n=2,915 launches, 2016-2019 and 2025; the pandemic years 2020-2023 are deliberately excluded. Outturn is US DOT DB1B for United States domestic routes and Sabre MIDT elsewhere."))

    # ---------------------------------------------------------------- 7
    add(S.divider("7", "The airport, the aircraft and the ask",
                  "What Genoa can do today, and what we are asking for",
                  image="divider.airport", family="field"))

    add(S.plate(
        slot="airport.aerial",
        subjects=["goa_airside", "goa_terminal", "genoa_airport"],
        section="Section 7 - The airport, the aircraft and the ask",
        title="One runway, on reclaimed land, inside the port",
        subtitle="The airport's geography is the reason the aircraft question has to be settled first",
        subject="Genoa Cristoforo Colombo from the air",
        credit="Aeroporto di Genova",
        date="to be supplied",
        supports="The single-runway departure constraint, this page",
        body=[("Why the geography matters",
               "Genoa Cristoforo Colombo is built on reclaimed land at Sestri Ponente, between the Ligurian sea and the hills, inside "
               "the port estate. It is a single-runway airport with no room to extend on either side, which is why the departure "
               "performance question is settled by an Airbus study rather than by a runway figure."),
              ("What we are not asserting",
               "No runway length or declared distance appears anywhere in this deck. Published sources differ by 150 metres and Avia "
               "does not print a figure it cannot source. The ENAV aerodrome chart settles it, and the Airbus performance study "
               "converts it into an answer.")],
        panels=[S.panel("The range case is already settled", [
                    "Genoa to New York is 3,509.6 nautical miles, circa 75% of the A321XLR's published 4,700 nm.",
                    "Shorter than Madrid to Boston, which has operated since 14 November 2024.",
                ], tone="accent")],
        source="Sources: ENAC airport register for the Sestri Ponente location; Airbus published range; Air Miles Calculator for the "
               "great-circle distance. Runway figures deliberately not quoted pending the ENAV aerodrome chart."))

    add(S.table(
        section="Section 7 - The airport, the aircraft and the ask",
        title="Genoa Cristoforo Colombo today",
        subtitle="The airport's position, and the two studies that complete the aircraft case",
        table={"head": ["Item", "Position"],
               "rows": [["Summer 2026 seat capacity, all routes", "1,375,000 seats, up 10% on summer 2025"],
                        ["Rank among Italian commercial airports", "19th of 44"],
                        ["Passengers, 2025", "1,587,761, up 18.1%, an all-time record"],
                        ["Widebody capability demonstrated", "An ITA A330-900neo operated in on 6 April 2026"],
                        ["Ownership", "Port authority 60%, Camera di Commercio di Genova 40%"],
                        ["Runway declared distances", "To be taken from the ENAV AIP chart for LIMJ"],
                        ["A321XLR performance at New York weight", "Airbus study to be commissioned"]],
               "widths": [3.4, 5.8]},
        panels=[S.panel("Why the two studies matter", [
                    "The range case is settled: 3,509.6 nm against a published 4,700 nm, shorter than Madrid to Boston.",
                    "The performance case is an aircraft-specific calculation that only Airbus can produce, and it is normal to commission it at this stage.",
                ], tone="accent")],
        source="Sources: ENAC, Air Traffic Data 2025, January 2026; GuidaViaggi reporting the airport operator, 19 March 2026; Genova24, 6 April 2026; Shipmag.it and Primocanale, 8 June 2026."))

    add(S.grid(
        section="Section 7 - The airport, the aircraft and the ask",
        title="What we will close before the carrier conversation",
        subtitle="Four items, three of which can be settled inside a quarter",
        rows=[("Catchment measurement",
               "A Sabre origin-destination pull keyed to Ligurian and western Lombard postcodes, sizing the demand airport by airport and carrier by carrier. Avia, circa a fortnight."),
              ("Aircraft performance",
               "An Airbus A321XLR study for departure at New York weight from Genoa's preferential runway in summer conditions. Commissioned by the airport."),
              ("Schedule and slots",
               "A New York end confirmed against slot availability at Newark and New York JFK, and a rotation built to the carrier's crew rules. Avia, with the carrier."),
              ("The funding package",
               "The launch package assembled across Regione Liguria, the Camera di Commercio, the port authority and the cruise and tourism sector, so it is on the table when the carrier is approached.")],
        accent_rows=[0, 1],
        callout=S.callout(["Next step: a working session with Regione Liguria and",
                           "the port authority, autumn 2026, to fund the studies"],
                          tone="dark"),
        source="Source: AviaSolutions analysis."))

    add(S.grid(
        section="Section 7 - The airport, the aircraft and the ask",
        title="Choose Genoa",
        subtitle="The case in six lines",
        rows=[("An existing corridor",
               "Circa 37% of Genoa and Savona port traffic is United States linked, and MSC already sails Genoa to New York direct in nine days."),
              ("Growing fastest",
               "Up 18.1% to 1,587,761 passengers in 2025, against Malpensa's 8.6% and Fiumicino's 4.5%."),
              ("A second gateway already at scale",
               "1,630,593 cruise passengers in 2025, more than the airport handled, worth EUR 346m to the local economy."),
              ("Within the aircraft",
               "3,509.6 nautical miles, circa 75% of the A321XLR's published range and shorter than Madrid to Boston."),
              ("A base, not a route",
               "Three United States points from one Genoa base fill 0.90 of a frame at a %s network margin." % p(t[4], 1)),
              ("Nobody else has moved",
               "The largest north-western Italian catchment with no United States service and no announced plan.")],
        accent_rows=[0, 4],
        source="Sources as cited on the preceding slides. Full citations in the Project Liguria evidence pack, 5 August 2026."))

    add(S.thanks("Thank you", "A direct link between Genoa and New York",
                 image="closing.frame", family="globe"))

    # ---------------------------------------------------------------- 8
    add(S.divider("8", "Appendix", "The assumptions register",
                  image="divider.appendix", family="instruments"))

    add(S.table(
        section="Appendix",
        title="Assumptions register",
        subtitle="Every input, its source and its status",
        table={"head": ["Input", "Source", "Status"],
               "rows": [["Catchment population and road times", "GeoNames population, OSRM road times", "Validated"],
                        ["New York market split and fares", "Sabre ODPOO 2024", "Validated"],
                        ["Fares, economy $345 and business $1,400 one-way", "Entrant-yield judgement", "Judgement"],
                        ["Cost stack", "Avia route economics module", "Directional"],
                        ["Maintenance", "Airbus 2024-2025 maintenance reserves", "Validated"],
                        ["Ownership", "Appraiser lease rates", "Directional"],
                        ["Jet fuel $0.90 per kilogramme", "Through-cycle planning assumption", "Tested $0.68 to $1.10"],
                        ["Crew $1,200 per block hour", "Low-cost-carrier judgement", "Judgement"],
                        ["Genoa and New York airport charges", "Indicative pending published tariffs", "To be confirmed"],
                        ["Monthly seasonality profile", "Leisure-weighted assumption", "Pending a monthly Sabre pull"]],
               "widths": [3.5, 3.4, 2.5]},
        source="Source: AviaSolutions assumptions register, Genoa - New York business case, 5 August 2026."))

    return S.paginate(d)


if __name__ == "__main__":
    spec = build()
    S.check(spec)
    print("slides:", len(spec["slides"]))
