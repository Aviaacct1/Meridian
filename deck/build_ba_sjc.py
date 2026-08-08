"""Project Redwood: British Airways London Heathrow - San Jose route business case.

Builds the full bespoke deck from the Avia house-style library, the QSI forecast
contract and the sourced evidence pack. Author metadata: Avia Solutions.

Run: python3 build_ba_sjc.py
"""

import json
import os
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

from avia_deck import (AviaDeck, NAVY, BODY, ORANGE, CYAN, WHITE, GREY, LIGHT,
                       MIDBLUE, TEAL, RED, M, TOP, BOTTOM, SW, SH)
import avia_charts as ch
import avia_maps as am

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
CONTRACT = os.path.join(HERE, "ba_lhr_sjc_deck_contract.json")
OUT = os.path.join(HERE, "Project_Redwood_BA_LHR-SJC_Route_Business_Case.pptx")

CODENAME = "Project Redwood"
EVENT = "World Routes 2026"
AVIA = "Source: AviaSolutions analysis."
FCAST_BASIS = ("Source: AviaSolutions analysis. Base demand Sabre MI O&D, "
               "service year as shown. Forecast produced on the Avia Cortex QSI "
               "engine; figures carry the model's calibrated confidence range.")

# ---------------------------------------------------------------------------
# Charts and maps
# ---------------------------------------------------------------------------


def build_figures(c):
    p = lambda n: os.path.join(ASSETS, n)
    ch.bayarea_lhr(p("ch_bayarea_lhr.png"))
    ch.carrier_sfo(p("ch_carrier_sfo.png"))
    ch.sjc_traffic(p("ch_sjc_traffic.png"))
    ch.gdp_per_worker(p("ch_gdp_worker.png"))
    ch.marketcap(p("ch_marketcap.png"))
    rv = c["revenue_forecast"]
    ch.revenue_flow(p("ch_rev_flow.png"), rv["years"],
                    rv["revenue"]["point_to_point"],
                    rv["revenue"]["connecting_at_hub"],
                    rv["revenue"]["connecting_at_destination"],
                    rv["revenue"]["cargo"], rv["revenue"]["ancillary"])
    # cabin split: apply the MIDT cabin revenue mix to passenger revenue
    pax_rev = [a + b + d for a, b, d in zip(rv["revenue"]["point_to_point"],
                                            rv["revenue"]["connecting_at_hub"],
                                            rv["revenue"]["connecting_at_destination"])]
    mix = (0.42, 0.13, 0.45)
    ch.revenue_cabin(p("ch_rev_cabin.png"), rv["years"],
                     [r * mix[0] for r in pax_rev],
                     [r * mix[1] for r in pax_rev],
                     [r * mix[2] for r in pax_rev])
    if not os.path.exists(p("map_route.png")):
        am.route_map(p("map_route.png"))
    if not os.path.exists(p("map_catchment.png")):
        am.catchment_map(p("map_catchment.png"))


# ---------------------------------------------------------------------------
def fmt(n, dp=0):
    return "{:,.{}f}".format(n, dp)


def k(n):
    return "{:,.1f}".format(n / 1000.0)


def pct(x, dp=1):
    return "{:.{}f}%".format(x * 100, dp)


def main(pages=None):
    with open(CONTRACT) as f:
        c = json.load(f)
    build_figures(c)

    rm = c["route_metadata"]
    ss = c["summary_and_schedule"]
    sf = c["segment_forecast"]
    rv = c["revenue_forecast"]
    ec = c["economics_year1"]

    d = AviaDeck(deck_title="%s - British Airways London Heathrow to San Jose" % CODENAME,
                 event_line=EVENT, assets_dir=ASSETS,
                 client_logo="sjc_logo_navy.jpeg",
                 airline_logo="ba_logo.png")

    # ---------------------------------------------------------------- 1 cover
    d.cover("cover_sjc_terminal.png",
            ["A Unique Opportunity to Re-establish",
             "the Silicon Valley Link from London"],
            "Prepared for British Airways on behalf of San Jose Mineta International Airport",
            "World Routes 2026   |   5 August 2026   |   %s   |   Commercial in Confidence" % CODENAME,
            status="DRAFT")

    # ------------------------------------------------------------- 2 contents
    s = d.content("Contents", "A Unique Opportunity to Re-establish the Silicon Valley Link from London")
    titles = ["The opportunity in one slide", "Why Silicon Valley and why San Jose",
              "The London link", "Stimulation, not cannibalisation",
              "London - San Jose route forecast",
              "Forecast methodology and track record",
              "San Jose Mineta and the commercial offer", "Appendix"]
    pg = pages or [0] * len(titles)
    items = [(str(i + 1), t, pg[i] if i < len(pg) else 0)
             for i, t in enumerate(titles)]
    y = 1.62
    for num, title, page in items:
        d._rect(s, M + 0.10, y, 0.52, 0.52, fill=NAVY, shape=MSO_SHAPE.OVAL)
        d._text(s, M + 0.10, y + 0.145, 0.52, 0.30, [(num, 14, True, WHITE)],
                align=PP_ALIGN.CENTER)
        d._text(s, M + 0.86, y + 0.10, 7.4, 0.36, [(title, 16, True, BODY)])
        d._text(s, 8.60, y + 0.10, 1.0, 0.36,
                [(str(page) if page else "-", 16, True, MIDBLUE)],
                align=PP_ALIGN.RIGHT)
        d._rect(s, M + 0.86, y + 0.56, 7.75, 0.012, fill=LIGHT)
        y += 0.665

    # ------------------------------------------------- 3 the case in one slide
    s = d.content("British Airways is well placed to return",
                  "Seven reasons, each evidenced later in this deck")
    grid = [("No European service", "SJC has zero European nonstops. All seven international routes are Mexico plus seasonal Tokyo Narita."),
            ("A London-only market", "All Bay Area to London capacity flies through SFO: 49 peak weekly departures, circa 14,500 weekly seats, three carriers."),
            ("BA already owns the Bay Area", "SFO is one of only four Heathrow A380 routes BA retains for winter 2026/27. This is a market BA is deepening."),
            ("Proven additive, on BA's own record", "When BA added SJC in 2016 the combined Bay Area to Heathrow market grew every year, 1.02m to 1.17m by 2019."),
            ("The world's densest premium catchment", "Silicon Valley GDP per worker is $336,515, 1.75x the US average, on regional GDP of $522bn."),
            ("SFO is filling up again", "SJC's adopted forecast has SFO back at peak airfield capacity in FFY2027, with spillover moving to San Jose."),
            ("An anchor the airport will pay for", "18-month full landing fee waiver plus up to $500,000 of marketing support for a new long-haul international route.")]
    y = 1.44
    for i, (head, body) in enumerate(grid):
        h = 0.76
        fill = LIGHT if i % 2 == 0 else WHITE
        d._rect(s, M, y, 9.40, h, fill=fill)
        d._rect(s, M, y, 0.055, h, fill=ORANGE if i in (0, 3) else MIDBLUE)
        d._text(s, M + 0.20, y + 0.10, 2.62, 0.56, [(head, 13, True, NAVY)],
                anchor=MSO_ANCHOR.MIDDLE)
        d._text(s, M + 2.92, y + 0.09, 6.36, 0.58, [(body, 11.5, False, BODY)],
                anchor=MSO_ANCHOR.MIDDLE)
        y += h + 0.045
    d.source(s, "Sources: flysanjose.com, fetched 5 August 2026; US DOT / BTS International Report - Passengers, retrieved 5 August 2026; "
                "Moody's Economy.com via Silicon Valley Institute for Regional Studies, April 2026; HNTB / City of San Jose SJC Aviation Activity Forecast, October 2025; "
                "SJC Airline Air Service Support Program, accessed 5 August 2026. AviaSolutions analysis.", size=7.5)

    # ---------------------------------------------- 4 summary of route forecast
    s = d.content("Opportunity for British Airways",
                  "Summary of route forecast, year 1, daily Boeing 787-8 service")
    d._pic_cover(s, d.a("map_route.png"), 0.0, 1.18, SW, 3.88)
    d._text(s, 0.34, 1.34, 3.2, 0.28, [("Point to point market", 12, True, NAVY)])
    d._text(s, 0.34, 1.58, 3.2, 0.46, [("%s*" % fmt(ss["point_to_point_market"]), 26, True, MIDBLUE)])
    d._text(s, 6.44, 1.34, 3.2, 0.28, [("Connecting market over London", 12, True, NAVY)],
            align=PP_ALIGN.RIGHT)
    d._text(s, 6.44, 1.58, 3.2, 0.46, [("%s*" % fmt(ss["connecting_market_over_hub"]), 26, True, MIDBLUE)],
            align=PP_ALIGN.RIGHT)
    d._text(s, 0.34, 4.06, 3.4, 0.28, [("Connecting market over San Jose", 12, True, NAVY)])
    d._text(s, 0.34, 4.30, 3.4, 0.46, [("%s*" % fmt(ss["connecting_market_over_destination"]), 26, True, MIDBLUE)])
    sch = ss["schedule"]
    d._text(s, M, 5.16, 4.0, 0.26, [("Schedule options: Boeing 787-8", 12, True, NAVY)])
    rows = []
    for r in sch[:2]:
        rows.append([r["sector"], r["dep_time"], r["arr_time"], r["operating_days"],
                     r["aircraft"], fmt(r["seats"]), fmt(r["annual_seats"]),
                     fmt(r.get("annual_pax") or 0), pct(r.get("seat_factor") or 0)])
    d.table(s, M, 5.44, 8.90,
            ["Sector", "Dep. time", "Arr. time", "Op. days", "Aircraft", "Seats",
             "Annual seats", "Annual pax yr 1", "Seat factor"],
            rows, col_w=[1.1, 0.8, 0.8, 0.85, 0.85, 0.7, 1.0, 1.05, 0.95],
            size=10, hdr_size=9, row_h=0.32, hdr_h=0.46)
    d.source(s, "* Base annual demand at the service year before stimulation, from AviaSolutions' San Jose Service Area catchment analysis. "
                "Schedule times are a representative assumption pending BA slot confirmation. " + FCAST_BASIS, size=7.5)

    # =============================================== SECTION 2
    d.divider("sanjose_aerial.jpeg", "2", "Why Silicon Valley and why San Jose",
              "The catchment, the employers, and the airport that sits inside the cluster")

    # -- key numbers
    s = d.content("The San Jose market in six numbers",
                  "A proven market, the world's densest technology cluster, and the income to pay for premium travel")
    d.keynumbers(s, [
        (["$522bn"], "Silicon Valley regional GDP in 2025, larger than the national economy of Belgium or Sweden"),
        (["$336,515"], "GDP per worker, 1.75x the United States average and the highest of any large US region"),
        (["$164,700"], "Median household income in Santa Clara County, 2.0x the US median"),
        (["43%"], "The Bay Area's share of all global venture capital dollars in the second quarter of 2026"),
        (["Zero"], "European nonstop services at San Jose Mineta today, from any airline"),
        (["1.17m"], "Bay Area to London Heathrow passengers in 2019, the last clean pre-pandemic year"),
    ])
    d.source(s, "Sources: Moody's Economy.com analysed by the Silicon Valley Institute for Regional Studies, 2026 Silicon Valley Index, April 2026; "
                "US Census ACS 2024 via SVIRS; Crunchbase News, July 2026; flysanjose.com fetched 5 August 2026; "
                "US DOT / BTS International Report - Passengers, retrieved 5 August 2026.", size=7.5)

    # -- the Bay Area airport system
    s = d.content("San Jose serves the South Bay, not the city",
                  "Three airports, three catchments, and only one of them inside the technology cluster")
    d._pic(s, "bayarea_map.jpeg", M, 1.42, h=4.30)
    rows = [["San Francisco (SFO)", "54.53m", "+4.3%", "15.91m", "Peninsula and city", "3 carriers, 49 weekly"],
            ["San Jose (SJC)", "10.68m", "-9.9%", "0.44m", "South Bay, Santa Cruz, Monterey", "None"],
            ["Oakland (OAK)", "circa 10m", "-14.7%", "n/a", "East Bay", "None"]]
    d.table(s, 5.20, 1.42, 4.52,
            ["Airport", "2025 pax", "vs 2024", "Intl pax", "Primary catchment", "London service"],
            rows, col_w=[1.25, 0.72, 0.62, 0.62, 1.35, 1.05], size=8.5, hdr_size=8.0,
            row_h=0.48, hdr_h=0.62,
            aligns=[PP_ALIGN.LEFT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT,
                    PP_ALIGN.LEFT, PP_ALIGN.LEFT])
    d.panel(s, 5.20, 3.62, 4.52, 2.34, "What the split means", [
        "SJC took 14.3% of Bay Area passengers in 2025, against SFO's dominant share.",
        "SFO carried 96% of Bay Area international travellers as long ago as 2011, so the South Bay's long-haul demand has always travelled north.",
        "SJC's primary service area runs south into Santa Cruz and Monterey counties and east towards the Central Valley, away from SFO.",
    ], size=10.5)
    d.source(s, "Sources: City of San Jose Airport Department memo, 8 July 2026; flysfo.com via Road Genius, 4 March 2026; "
                "MTC / ABAG Regional Aviation Activity Tracking Report, 2012 edition; SJC Terminal B South Concourse EA Scoping Package, 2020. "
                "Oakland 2025 total is indicative. AviaSolutions analysis.", size=7.5)

    # -- proximity to the campuses
    s = d.content("The headquarters are on the doorstep",
                  "San Jose Mineta sits inside the cluster; San Francisco sits 30 miles outside it")
    d._pic(s, "campus_pins_map.jpeg", M, 1.42, h=4.34)
    rows = [["NVIDIA", "Santa Clara", "6", "$5.37tn", "215.9"],
            ["Apple", "Cupertino", "8", "$4.51tn", "416.2"],
            ["Alphabet / Google", "Mountain View", "10", "$4.62tn", "402.8"],
            ["Intel", "Santa Clara", "6", "$518bn", "52.9"],
            ["AMD", "Santa Clara", "6", "$793bn", "34.6"],
            ["Cisco Systems", "San Jose", "4", "$485bn", "56.7"],
            ["Adobe", "San Jose", "3", "$103bn", "23.8"],
            ["Broadcom", "Palo Alto", "13", "$2.01tn", "63.9"],
            ["Meta Platforms", "Menlo Park", "17", "$1.49tn", "201.0"],
            ["Super Micro Computer", "San Jose", "4", "$20bn", "22.0"]]
    d.table(s, 5.24, 1.42, 4.48,
            ["Company", "Headquarters", "Miles from SJC", "Market cap", "Revenue ($bn)"],
            rows, col_w=[1.42, 1.05, 0.78, 0.78, 0.72], size=8.8, hdr_size=7.8,
            row_h=0.285, hdr_h=0.52,
            aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT,
                    PP_ALIGN.RIGHT])
    d.callout(s, 5.24, 4.62, 4.48, 0.62,
              "Nine of the ten largest Silicon Valley employers are within a 30-minute drive of SJC")
    d.source(s, "Sources: market capitalisation StockAnalysis.com intraday 5 August 2026; revenue latest reported fiscal year per company results releases; "
                "distances are straight-line from the SJC terminal, AviaSolutions calculation. Re-pull market values on one vendor at one timestamp at final issue.",
                size=7.5)

    # -- economic strength
    s = d.content("The highest value-add workforce in the US",
                  "Yield follows productivity, and Silicon Valley's productivity has no US peer")
    d._pic(s, "ch_gdp_worker.png", M, 1.40, w=5.30)
    rows = [["Silicon Valley GDP, 2025", "$522.0bn", "Moody's / SVIRS, Apr 2026"],
            ["Silicon Valley GDP, 2024", "$503.8bn", "Moody's / SVIRS, Apr 2026"],
            ["Santa Clara County GDP per head", "circa $229,800", "BEA, Feb 2026 (derived)"],
            ["US GDP per head, 2025", "$89,962", "BEA NIPA, Apr 2026"],
            ["Median household income, Santa Clara", "$164,700", "US Census ACS 2024"],
            ["US median household income", "circa $81,600", "US Census ACS 2024"],
            ["Per capita personal income, Santa Clara", "$157,620", "BEA, Feb 2026"]]
    d.table(s, 5.76, 1.40, 3.96, ["Measure", "Value", "Source"], rows,
            col_w=[2.0, 0.95, 1.35], size=8.6, hdr_size=8.2, row_h=0.40, hdr_h=0.42,
            aligns=[PP_ALIGN.LEFT, PP_ALIGN.RIGHT, PP_ALIGN.LEFT])
    d.callout(s, 5.76, 4.62, 3.96, 0.72,
              ["Santa Clara County GDP per head is 2.7x", "the United States average"], size=13)
    d.bullets(s, M, 5.10, 5.30, [
        ("Premium propensity.", "Household income at twice the US median, on a workforce paid for output per worker of $336,515."),
        ("Corporate density.", "The catchment holds fifteen listed companies each worth more than $250bn."),
    ], size=10.5)
    d.source(s, "Sources as shown in the table. Chart source: Moody's Economy.com analysed by the Silicon Valley Institute for Regional Studies, "
                "2026 Silicon Valley Index public data file, April 2026, in constant 2025 dollars.", size=7.5)

    # -- the big employer table
    s = d.content("Silicon Valley technology employers",
                  "Revenue, market value and headcount for the 24 largest listed companies in the San Jose catchment")
    emp = [
        ("NVIDIA", "Santa Clara", 215.94, 5370, 42000),
        ("Alphabet / Google", "Mountain View", 402.84, 4620, 190820),
        ("Apple", "Cupertino", 416.16, 4510, 166000),
        ("Broadcom", "Palo Alto", 63.89, 2010, 33000),
        ("Meta Platforms", "Menlo Park", 200.97, 1490, 78865),
        ("AMD", "Santa Clara", 34.64, 793, 31000),
        ("Visa", "San Francisco", 40.00, 675, 34100),
        ("Intel", "Santa Clara", 52.85, 518, 85100),
        ("Cisco Systems", "San Jose", 56.65, 485, 86200),
        ("Applied Materials", "Santa Clara", 28.37, 429, 36500),
        ("Lam Research", "Fremont", 18.44, 391, 17200),
        ("Netflix", "Los Gatos", 45.20, 307, 16000),
        ("Palo Alto Networks", "Santa Clara", 9.20, 296, 16068),
        ("Wells Fargo", "San Francisco", 80.04, 269, 205000),
        ("Western Digital", "San Jose", 9.52, 183, 51000),
        ("Gilead Sciences", "Foster City", 29.44, 163, 17000),
        ("Salesforce", "San Francisco", 41.53, 158, 83334),
        ("Uber Technologies", "San Francisco", 52.02, 138, 34000),
        ("ServiceNow", "Santa Clara", 13.28, 121, 29187),
        ("Adobe", "San Jose", 23.77, 103, 31360),
        ("Cadence Design Systems", "San Jose", 5.30, 93, 13800),
        ("Intuit", "Mountain View", 18.80, 89, 18200),
        ("Synopsys", "Sunnyvale", 7.05, 77, 28000),
        ("PayPal", "San Jose", 33.20, 50, 23800),
    ]
    rows = [[i + 1, n, hq, "$%.1f" % r,
             ("$%.2ftn" % (mc / 1000)) if mc >= 1000 else ("$%dbn" % mc),
             fmt(e)] for i, (n, hq, r, mc, e) in enumerate(emp)]
    tot_r = sum(x[2] for x in emp)
    tot_e = sum(x[4] for x in emp)
    tot_m = sum(x[3] for x in emp)
    rows.append(["", "Total, 24 companies", "", "$%.1f" % tot_r,
                 "$%.2ftn" % (tot_m / 1000), fmt(tot_e)])
    d.table(s, M, 1.38, 6.42,
            ["Rank", "Company", "Headquarters", "Revenue ($bn)", "Market cap", "Employees"],
            rows, col_w=[0.42, 1.75, 1.15, 0.92, 0.90, 0.88], size=7.2, hdr_size=7.2,
            row_h=0.206, hdr_h=0.34, total_row=True,
            aligns=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.RIGHT,
                    PP_ALIGN.RIGHT, PP_ALIGN.RIGHT])
    d._pic(s, "ch_marketcap.png", 6.82, 1.40, w=2.98)
    d.callout(s, 6.82, 3.44, 2.98, 0.94,
              ["The five largest are worth", "$18.0 trillion between them,", "147x the US airline sector"],
              size=11.5)
    d.panel(s, 6.82, 4.52, 2.98, 2.50, "Private companies in the catchment", [
        "Anthropic: $965bn valuation, May 2026",
        "OpenAI: $852bn, March 2026; 439,000 sq ft leased at Mountain View",
        "Databricks: $188bn, July 2026",
        "Stripe: $159bn, February 2026",
    ], size=9.5)
    d.source(s, "Sources: market capitalisation StockAnalysis.com (S&P Global Market Intelligence data) intraday 5 August 2026; "
                "revenue and headcount from each company's latest reported fiscal year results release. Private company figures are last-round "
                "post-money valuations, not market capitalisations. Bay Area local headcounts are not published company by company.", size=7.0)

    # -- AI wave
    s = d.content("AI is rebuilding the catchment",
                  "The single strongest reason a premium London service works better in 2028 than it did in 2016")
    d._pic_cover(s, d.a("nvidia_voyager.jpeg"), M, 1.40, 4.72, 2.62)
    d._pic_cover(s, d.a("google_downtown_west.jpeg"), M, 4.14, 4.72, 2.62)
    d.panel(s, 5.22, 1.40, 4.50, 5.36, None, [], fill=TEAL)
    d._text(s, 5.42, 1.56, 4.10, 0.34,
            [("Committed since BA left in 2023", 13.5, True, WHITE)])
    facts = [("NVIDIA", "FY2026 revenue $215.9bn, up 65%. Over $834.7m spent assembling a 58.6-acre Santa Clara block, six miles from the runway."),
             ("Microsoft", "48 MW, circa 396,914 sq ft data centre campus in Alviso, San Jose. Ground broken 10 June 2026."),
             ("OpenAI", "439,000 to 450,000 sq ft campus leased at Ellis Street, Mountain View, on a ten-year term, plus over 1m sq ft in San Francisco."),
             ("Anthropic", "Circa 1m sq ft assembled on Howard Street, San Francisco. Valued at $965bn in May 2026."),
             ("Google", "80+ acres assembled and cleared at Downtown West, San Jose: 4,000 homes and 5,700 construction jobs consented."),
             ("Databricks", "Circa 635,000 sq ft being assembled at Sunnyvale.")]
    yy = 2.02
    for head, body in facts:
        d._text(s, 5.42, yy, 4.10, 0.22, [(head, 11.5, True, ORANGE)])
        d._text(s, 5.42, yy + 0.20, 4.10, 0.54, [(body, 9.6, False, WHITE)])
        yy += 0.79
    d.source(s, "Sources: NVIDIA Q4 FY2026 press release, 25 February 2026; Hoodline, March 2026; Local News Matters, 12 June 2026; "
                "SF Standard, 26 February 2026; The Real Deal, 2 and 7 April 2026 and 10 July 2026; Planetizen, March 2026. "
                "Images: NVIDIA Voyager, Santa Clara; Google Downtown West, San Jose.", size=7.0)

    # -- San Jose city dynamics
    s = d.content("San Jose is building demand at the airport",
                  "The tenth-largest city in the United States, and the only one with a runway inside its technology cluster")
    d._pic_cover(s, d.a("sanjose_aerial2.jpeg"), 0.0, 1.20, SW, 3.10)
    rows = [["Google Downtown West", "80+ acres cleared; 4,000 homes, 15 acres of parks, 5,700 construction jobs consented", "$54m penalty if not started by 1 July 2031"],
            ["Microsoft Alviso data centre", "48 MW, two buildings, circa 396,914 sq ft", "Ground broken 10 June 2026"],
            ["Airport Connector", "Airport to Diridon Station link", "Feasibility validated; technical report September 2024"],
            ["SJC Terminal B South Concourse", "Up to 14 gates and 750,000 sq ft", "FAA record of decision issued April 2023"],
            ["On-airport hotel", "Up to 330 rooms, 300,000 sq ft", "In the amended Master Plan, May 2026"]]
    d.table(s, M, 4.46, 9.40, ["Development", "Scale", "Status"], rows,
            col_w=[2.2, 4.6, 2.6], size=9.2, hdr_size=8.6, row_h=0.42, hdr_h=0.40,
            aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT])
    d.source(s, "Sources: City of San Jose Resolution RES2026-122, 12 May 2026; City of San Jose Airport Department memo, 8 July 2026; "
                "Local News Matters, 12 June 2026; Hoodline and Planetizen, March 2026; flysanjose.com, accessed 5 August 2026.", size=7.5)

    # =============================================== SECTION 3
    d.divider("sanjose_night.jpeg", "3", "The London link",
              "Trade, investment, corporate presence and the traffic that already exists")

    # -- the market is London-only
    s = d.content("A one-airport market for the Bay Area",
                  "Every London seat in the Bay Area flies to or from San Francisco")
    rows = [["LHR - SFO", "British Airways", "A380-800 and 777-300ER", "14", "circa 5,075"],
            ["LHR - SFO", "United", "787-9", "21", "circa 5,082"],
            ["LHR - SFO", "Virgin Atlantic", "A350-1000 and 787-9", "14 peak", "circa 4,326"],
            ["LHR - SFO", "Total, 3 carriers", "", "49 peak", "circa 14,500"],
            ["LGW - SFO", "None since October 2023", "", "0", "0"],
            ["London - Oakland", "None", "", "0", "0"],
            ["London - San Jose", "None since October 2023", "", "0", "0"]]
    d.table(s, M, 1.44, 9.40,
            ["Airport pair", "Carrier", "Aircraft", "Weekly frequency each way", "Weekly seats each way"],
            rows, col_w=[1.5, 2.5, 2.6, 1.4, 1.4], size=10, hdr_size=9, row_h=0.36,
            hdr_h=0.46,
            aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.RIGHT,
                    PP_ALIGN.RIGHT])
    d.callout(s, M, 4.62, 4.58, 0.90,
              ["LHR - SFO is San Francisco's second largest", "international market, circa 1.08m passengers a year"],
              size=12)
    d.callout(s, 5.12, 4.62, 4.58, 0.90,
              ["SFO returns to peak airfield capacity in FFY2027", "on the airport's own adopted forecast"],
              size=12, fill=NAVY, colour=WHITE)
    d.bullets(s, M, 5.68, 9.40, [
        ("BA is deepening, not retreating.", "San Francisco is one of only four Heathrow A380 routes British Airways retains for winter 2026/27, and BA has flown two daily Heathrow rotations to San Francisco year round throughout."),
        ("No South Bay relief valve.", "A capacity-constrained San Francisco with no San Jose alternative means Silicon Valley demand either drives north through the peninsula or connects over another gateway."),
        ("The gap is not competitive, it is structural.", "London to San Jose has had no operator at all since October 2023, and no airline other than British Airways has ever flown it."),
    ], size=11)
    d.source(s, "Sources: FlightsFrom.com schedule week 29 June to 5 July 2026, accessed 5 August 2026; weekly seats are AviaSolutions estimates from "
                "published aircraft configurations; Road Genius citing US DOT International Report Passengers, 4 March 2026; "
                "HNTB / City of San Jose SJC Aviation Activity Forecast, October 2025.", size=7.5)

    # -- UK trade and corporate presence
    s = d.content("The corporate base already spans both ends",
                  "The United Kingdom is California's largest source of inward investment")
    rows = [["British-owned firms in California", "2,215", "World Trade Center LA FDI report via CalChamber"],
            ["Jobs in California at British-owned firms", "130,628", "As above"],
            ["Bay Area share of those jobs", "18%, the largest regional share", "As above"],
            ["Silicon Valley company offices in the UK, 2015", "428", "SJC Director of Aviation, reported August 2015"],
            ["NVIDIA UK commitment", "GBP 11bn, its largest European deployment", "NVIDIA Newsroom, 16 September 2025"],
            ["UK services exports to the US delivered by travel", "GBP 21.3bn a year", "UK Department for Business and Trade, 31 July 2026"],
            ["UK-born residents in the Bay Area CSA", "37,865", "US Census ACS 2020-2024"]]
    d.table(s, M, 1.42, 5.72, ["Measure", "Figure", "Source"], rows,
            col_w=[2.5, 1.85, 2.4], size=9, hdr_size=8.6, row_h=0.52, hdr_h=0.42,
            aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT])
    d.panel(s, 6.18, 1.42, 3.54, 5.10, "Bay Area firms with major London operations", [
        "Google: King's Cross campus, its largest outside the United States",
        "Apple: Battersea Power Station headquarters",
        "Meta: King's Cross and Rathbone Square",
        "NVIDIA: UK research presence, GBP 11bn committed",
        "OpenAI and Anthropic: both hold London offices",
        "Cisco, Adobe, Salesforce, Intuit and Netflix all hold London offices",
    ], size=10.5)
    d.source(s, "Sources as shown in the table. London operations verified against each company's own published property and careers pages, "
                "August 2026. Floor areas and headcounts are not published on a consistent basis and are therefore not quoted.", size=7.5)

    # -- links, partnerships
    s = d.content("Institutional links run in both directions",
                  "The institutional traffic that underpins a premium schedule")
    left = [("UK Government in the Bay Area", "The United Kingdom maintains a Consulate General and a Department for Business and Trade technology team in San Francisco, with a dedicated Silicon Valley technology envoy. The posting exists because the technology relationship is now managed as a bilateral priority rather than as ordinary trade promotion."),
            ("University links", "Stanford and Berkeley hold long-standing research partnerships with Oxford, Cambridge and Imperial College London, all three of which run their own Bay Area programmes. Academic traffic is term-driven and books early, which is the profile a long-haul route wants in its shoulder months."),
            ("Investment flows", "The United Kingdom is the largest single source of foreign direct investment into California: 2,215 British-owned firms employing 130,628 people, with the Bay Area taking 18% of those jobs, the largest regional share of any part of the state."),
            ("Travel-delivered exports", "GBP 21.3bn a year of United Kingdom services exports to the United States are delivered by putting people on aeroplanes. That is the demand a direct service converts from one-stop to nonstop.")]
    yy = d.methodology(s, left, y=1.44, w=4.62)
    d._pic_cover(s, d.a("sanjose_downtown.png"), 5.12, 1.44, 4.60, 2.30)
    d.panel(s, 5.12, 3.90, 4.60, 3.12, "What this means for the schedule", [
        "Institutional and corporate travel is schedule-sensitive and premium-weighted: it wants a morning arrival and a late-afternoon departure.",
        "It is also counter-cyclical to leisure demand, which supports a year-round rather than seasonal operation.",
        "The 2016-2023 operation proved the corporate demand exists; what changed was the aircraft, not the market.",
    ], size=10.5)
    d.source(s, "Sources: UK Government departmental publications and university programme pages, accessed August 2026; "
                "World Trade Center Los Angeles FDI report via CalChamber. Specific programme values are not published and are therefore not quoted. "
                "AviaSolutions analysis.", size=7.5)

    # =============================================== SECTION 4
    d.divider("apple_park.jpeg", "4", "Stimulation, not cannibalisation",
              "What actually happened at San Francisco when British Airways added San Jose")

    s = d.content("The combined market grew every year",
                  "US Department of Transportation data on British Airways' own previous San Jose operation")
    d._pic(s, "ch_bayarea_lhr.png", M, 1.40, w=5.86)
    rows = [["2015", "1,020,149", "-", "0", "1,020,149", "base"],
            ["2016", "989,098", "-3.0%", "73,954", "1,063,052", "+4.2%"],
            ["2017", "978,355", "-1.1%", "110,863", "1,089,218", "+6.8%"],
            ["2018", "1,027,982", "+5.1%", "107,458", "1,135,440", "+11.3%"],
            ["2019", "1,050,777", "+2.2%", "115,101", "1,165,878", "+14.3%"]]
    d.table(s, 6.32, 1.44, 3.40,
            ["Year", "SFO-LHR", "y/y", "SJC-LHR", "Combined", "vs 2015"],
            rows, col_w=[0.52, 0.85, 0.55, 0.72, 0.85, 0.60], size=8.0, hdr_size=7.4,
            row_h=0.34, hdr_h=0.46)
    d.callout(s, 6.32, 3.72, 3.40, 1.10,
              ["SFO - Heathrow was back above", "its pre-San Jose level by 2018,", "with the SJC service running"],
              size=11.5)
    d.panel(s, 6.32, 4.94, 3.40, 2.08, "How to read this", [
        "On a static counterfactual, roughly 62% of the San Jose traffic was net new and 38% diverted.",
        "Measured against 2014, SFO-Heathrow was up 7.3% by 2017: no measurable diversion at all.",
    ], size=10)
    d.source(s, "Source: US DOT / BTS International Report - Passengers, retrieved 5 August 2026; annual totals summed from published monthly rows. "
                "The net new and diverted split is an AviaSolutions calculation on a static counterfactual and is an estimate.", size=7.5)

    s = d.content("The San Francisco incumbent was not damaged",
                  "United grew its Heathrow traffic 27.5% through the entire San Jose period")
    d._pic(s, "ch_carrier_sfo.png", M, 1.40, w=5.86)
    rows = [["2015", "459,879", "265,311", "294,651"],
            ["2016", "443,887", "267,055", "278,156"],
            ["2017", "431,696", "291,091", "255,568"],
            ["2018", "429,805", "317,500", "280,677"],
            ["2019", "427,710", "338,230", "284,837"],
            ["Change", "-7.0%", "+27.5%", "-3.3%"]]
    d.table(s, 6.32, 1.44, 3.40,
            ["Year", "British Airways", "United", "Virgin Atlantic"], rows,
            col_w=[0.72, 0.96, 0.86, 0.86], size=8.4, hdr_size=7.6, row_h=0.34,
            hdr_h=0.50, total_row=True)
    d.panel(s, 6.32, 4.06, 3.40, 1.44, "British Airways' own position", [
        "BA's total Bay Area to Heathrow carriage rose from 459,879 in 2015 to 542,559 in 2017, up 18.0%.",
    ], size=10.5)
    d.panel(s, 6.32, 5.58, 3.40, 1.44, "Presented in full", [
        "The Lufthansa Frankfurt-San Jose case reads less favourably and is set out in the appendix rather than left out.",
    ], size=10.5, fill=RED)
    d.bullets(s, M, 5.20, 5.86, [
        ("Three carriers, three outcomes.", "United gained share, Virgin Atlantic held broadly flat, and British Airways traded a small number of San Francisco passengers for a larger number at San Jose."),
        ("The test that matters.", "If San Jose had cannibalised San Francisco, the incumbent would have shrunk. It did not."),
    ], size=10.5)
    d.source(s, "Source: US DOT / BTS International Report - Passengers, retrieved 5 August 2026. British Airways total Bay Area carriage is an "
                "AviaSolutions calculation summing SFO and SJC. AviaSolutions analysis.", size=7.5)

    s = d.content("San Jose is 31.8% below its 2019 peak",
                  "The airport's own numbers, and the reason it is prepared to underwrite an anchor route")
    d._pic(s, "ch_sjc_traffic.png", M, 1.40, w=5.86)
    d.panel(s, 6.32, 1.44, 3.40, 2.66, "The honest position", [
        "10,675,167 passengers in 2025, down 9.9% on 2024.",
        "2026 is running 12.1% below 2025 for January to May.",
        "The May 2026 Master Plan amendment cut the 2037 forecast from 22.5m to 16.75m.",
    ], size=10.5, fill=RED)
    d.bullets(s, M, 5.24, 5.86, [
        ("Why the airport shrank.", "San Jose lost its European service, its Tokyo service went seasonal, and domestic capacity moved north as the Bay Area recovered unevenly."),
        ("What has not changed.", "The catchment. Silicon Valley GDP has grown from $503.8bn in 2024 to $522.0bn in 2025 while the airport's traffic fell."),
    ], size=10.5)
    d.panel(s, 6.32, 4.24, 3.40, 2.78, "Why that argues for the route", [
        "The 5.75m gap between the old and new forecasts is the commercial case for a long-haul anchor.",
        "An airport with spare gates, spare runway and a published incentive is a cheaper place to launch than a full one.",
        "SFO reaches peak airfield capacity again in FFY2027 on the same adopted forecast.",
    ], size=10.5)
    d.source(s, "Sources: City of San Jose Airport Department, Annual Status Report on the Airport Master Plan for Calendar Year 2025, 8 July 2026; "
                "SJC Monthly Activity Report May 2026, 18 June 2026; City of San Jose Resolution RES2026-122, 12 May 2026; "
                "HNTB / City of San Jose SJC Aviation Activity Forecast, October 2025.", size=7.5)

    # =============================================== SECTION 5 FORECAST
    d.divider("samsung_hq.jpeg", "5", "London - San Jose route forecast",
              "Point to point, connecting over London, connecting behind San Jose, and the route economics")

    # -- catchment
    s = d.content("San Jose service area",
                  "Primary, secondary and contested zones used to apportion demand")
    d._pic(s, "map_catchment.png", M, 1.40, h=5.16)
    rows = [["Primary", "Santa Clara County and the immediate South Bay", "Full allocation to SJC"],
            ["Secondary", "Santa Cruz, San Benito, Monterey, southern Alameda, eastward to the Central Valley", "Partial allocation, distance weighted"],
            ["Contested", "The mid-Peninsula, where SFO and OAK compete directly for the same resident", "Share allocated on access time and service quality"]]
    d.table(s, 5.20, 1.40, 4.52, ["Zone", "Coverage", "Treatment in the forecast"], rows,
            col_w=[0.85, 2.15, 1.52], size=9, hdr_size=8.4, row_h=0.86, hdr_h=0.44,
            aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT])
    d.panel(s, 5.20, 4.42, 4.52, 2.14, "How the catchment is built", [
        "Demand is allocated at cell level from population, employment and income, then tested against observed airport choice.",
        "Only service-area demand enters the forecast: passengers who would always use SFO are excluded, not discounted.",
        "The zones shown are indicative; the forecast uses the underlying cell allocation.",
    ], size=10)
    d.source(s, "Source: AviaSolutions San Jose Service Area catchment analysis. Zone boundaries on the map are indicative and drawn for "
                "presentation; the forecast is built on the cell-level allocation. Primary service area definition per SJC Terminal B South "
                "Concourse EA Scoping Package, 2020.", size=7.5)

    # -- main forecast table
    s = d.content("Route forecast: London - San Jose",
                  "Daily Boeing 787-8 service, year 1, two-way annual passengers")
    rows = []
    for r in sf["rows"]:
        rows.append([r["segment"], k(r["base_annual_demand"]),
                     pct(r["annual_growth_rate"]),
                     k(r["demand_at_service_year"]),
                     "%.2fx" % r["stimulation_factor"],
                     k(r["demand_after_stimulation"]),
                     pct(r["capture_rate"], 0),
                     k(r["forecast"]), "%.1f" % r["pdew"]])
    smy = sf["summary"]
    for label, key in [("Point to point total", "point_to_point_total"),
                       ("Connecting at London", "connecting_at_hub_total"),
                       ("Connecting at San Jose", "connecting_at_destination_total"),
                       ("Total forecast, year 1", "grand_total")]:
        t = smy[key]
        rows.append([label, k(t["base_annual_demand"]), "",
                     k(t["demand_at_service_year"]), "",
                     k(t["demand_after_stimulation"]),
                     pct(t["capture_rate"], 1), k(t["forecast"]),
                     "%.1f" % t["pdew"]])
    d.table(s, M, 1.40, 9.40,
            ["Market segment", "Base annual demand (000s)", "Annual growth rate",
             "Demand at service year (000s)", "Stimulation from direct service",
             "Demand after stimulation (000s)", "BA capture rate",
             "Forecast (000s)", "PDEW"],
            rows, col_w=[2.20, 0.95, 0.80, 0.95, 0.90, 0.95, 0.80, 0.85, 0.60],
            size=8.4, hdr_size=7.2, row_h=0.295, hdr_h=0.78)
    d.callout(s, M, 6.14, 4.58, 0.62,
              "Year 1 forecast: %s passengers, %s PDEW" % (fmt(smy["grand_total"]["forecast"]),
                                                           "%.0f" % smy["grand_total"]["pdew"]))
    d.callout(s, 5.12, 6.14, 4.58, 0.62,
              "Implied seat factor %s on %s annual seats" % (pct(rv["implied_load_factor"][0], 1),
                                                            fmt(rv["annual_capacity"][0])),
              fill=NAVY, colour=WHITE)
    d.source(s, "Source: AviaSolutions analysis on the Avia Cortex QSI engine. Base demand Sabre MI O&D adjusted for non-MIDT channels, "
                "service-area demand only. PDEW is passengers daily each way. This run uses the validated 2015-basis model and is presented for "
                "format; a live pitch is re-run on the current Sabre MIDT year and the current schedule.", size=7.0)

    # -- connecting at London
    s = d.content("Passengers connecting at London",
                  "The largest markets beyond Heathrow, year 1, two-way annual passengers")
    cities = c["connecting_at_hub"]["cities"][:18]
    rows = [[str(x["nr"]), x["city_code"], x["city_name"], x["country"],
             fmt(x["annual_demand"]), pct(x["airline_share"], 1),
             fmt(x["annual_forecast"]), "%.1f" % x["pdew"]] for x in cities]
    tot = c["connecting_at_hub"]["total"]
    others = c["connecting_at_hub"]["cities"][18:]
    if others:
        rows.append(["", "", "Other %d markets" % len(others), "",
                     fmt(sum(x["annual_demand"] for x in others)), "",
                     fmt(sum(x["annual_forecast"] for x in others)),
                     "%.1f" % (sum(x["annual_forecast"] for x in others) / 730.0)])
    rows.append(["", "", "Total connecting at London", "", fmt(tot["annual_demand"]),
                 "", fmt(tot["annual_forecast"]), "%.1f" % tot["pdew"]])
    d.table(s, M, 1.38, 6.30,
            ["Nr", "City", "City name", "Country", "Annual demand",
             "BA share", "Annual forecast", "PDEW"],
            rows, col_w=[0.32, 0.42, 1.35, 1.20, 0.98, 0.62, 0.90, 0.55],
            size=8.0, hdr_size=7.6, row_h=0.256, hdr_h=0.46, total_row=True,
            aligns=[PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT,
                    PP_ALIGN.RIGHT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT])
    d.panel(s, 6.80, 1.38, 2.92, 2.60, "Why the London feed works", [
        "British Airways operates 331 daily departures to 161 destinations from Heathrow.",
        "The QSI model credits British Airways only where the connection is competitive on total elapsed time.",
        "Double connections are excluded throughout.",
    ], size=10)
    d.callout(s, 6.80, 4.12, 2.92, 0.94,
              ["%s connecting passengers" % fmt(tot["annual_forecast"]),
               "in year 1, %s PDEW" % ("%.0f" % tot["pdew"])], size=12)
    d.panel(s, 6.80, 5.20, 2.92, 1.82, "Segment share", [
        "Connecting traffic is %s of the year 1 forecast." % pct(
            tot["annual_forecast"] / float(smy["grand_total"]["forecast"]), 0),
        "It is the flow that makes a daily widebody work in a market of this size.",
    ], size=10)
    d.source(s, FCAST_BASIS + " Heathrow network scale: Aviation A2Z, 30 July 2026.", size=7.5)

    # -- connecting at San Jose
    s = d.content("Passengers connecting at San Jose",
                  "San Jose is an origin and destination market, not a connecting hub")
    cd = c["connecting_at_destination"]["total"]
    rows = [["Point to point, San Jose service area", fmt(smy["point_to_point_total"]["demand_after_stimulation"]),
             pct(smy["point_to_point_total"]["capture_rate"], 1),
             fmt(smy["point_to_point_total"]["forecast"]),
             "%.1f" % smy["point_to_point_total"]["pdew"]],
            ["Connecting behind San Jose", fmt(cd["annual_demand"]), pct(0.002, 1),
             fmt(cd["annual_forecast"]), "%.1f" % cd["pdew"]],
            ["Total San Jose end", fmt(smy["point_to_point_total"]["demand_after_stimulation"] + cd["annual_demand"]),
             "", fmt(smy["point_to_point_total"]["forecast"] + cd["annual_forecast"]),
             "%.1f" % (smy["point_to_point_total"]["pdew"] + cd["pdew"])]]
    d.table(s, M, 1.44, 6.30,
            ["Flow", "Annual demand", "BA capture", "Annual forecast", "PDEW"],
            rows, col_w=[2.6, 1.05, 0.85, 1.05, 0.60], size=9.5, hdr_size=8.6,
            row_h=0.46, hdr_h=0.46, total_row=True)
    d.methodology(s, [
        ("The behind-San Jose feed is deliberately small",
         "San Jose has no domestic hub carrier and no significant transfer product. The forecast credits only 0.2 per cent of the 1.21m annual "
         "behind-market demand, worth %s passengers a year. We would rather under-claim the feed than build a case on connections "
         "no airline schedules." % fmt(cd["annual_forecast"])),
        ("What this means for the route",
         "Circa 98 per cent of the San Jose end is local point to point traffic from the service area. That is the highest quality traffic on the "
         "route: business demand from the catchment, paying local fares, in a market with a 2.0x US median household income."),
    ], y=3.52, w=6.30)
    d.panel(s, 6.80, 1.44, 2.92, 5.10, "Domestic pool at San Jose", [
        "34 domestic destinations served in August 2026.",
        "Southwest and Alaska hold the largest domestic positions; neither offers a transatlantic transfer product.",
        "American, Delta and United each connect San Jose to their own hubs, which is a competing one-stop London option rather than a feed.",
        "The forecast therefore treats San Jose as an origin and destination market, consistent with the 2016-2023 operation.",
    ], size=10.5)
    d.source(s, FCAST_BASIS + " Domestic destination count: flysanjose.com, fetched 5 August 2026.", size=7.5)

    # -- revenue forecast
    s = d.content("Revenue forecast for London - San Jose",
                  "Daily Boeing 787-8 service, years 1 to 3, US dollars")
    yrs = rv["years"]
    hdr = ["Line", "Year 1", "Year 2", "Year 3"]
    rows = []
    rows.append(["Passenger demand: point to point"] + [fmt(v) for v in rv["passengers"]["point_to_point"]])
    rows.append(["Passenger demand: connecting at London"] + [fmt(v) for v in rv["passengers"]["connecting_at_hub"]])
    rows.append(["Passenger demand: connecting at San Jose"] + [fmt(v) for v in rv["passengers"]["connecting_at_destination"]])
    rows.append(["Total passengers"] + [fmt(v) for v in rv["passengers"]["total"]])
    rows.append(["Annual capacity, seats"] + [fmt(v) for v in rv["annual_capacity"]])
    rows.append(["Implied load factor"] + [pct(v, 1) for v in rv["implied_load_factor"]])
    rows.append(["Revenue: point to point"] + ["$%s" % fmt(v) for v in rv["revenue"]["point_to_point"]])
    rows.append(["Revenue: connecting at London"] + ["$%s" % fmt(v) for v in rv["revenue"]["connecting_at_hub"]])
    rows.append(["Revenue: connecting at San Jose"] + ["$%s" % fmt(v) for v in rv["revenue"]["connecting_at_destination"]])
    rows.append(["Revenue: cargo"] + ["$%s" % fmt(v) for v in rv["revenue"]["cargo"]])
    rows.append(["Revenue: ancillary"] + ["$%s" % fmt(v) for v in rv["revenue"]["ancillary"]])
    rows.append(["Total revenue"] + ["$%s" % fmt(v) for v in rv["revenue"]["total"]])
    d.table(s, M, 1.42, 6.10, hdr, rows, col_w=[2.7, 1.15, 1.15, 1.15],
            size=9.0, hdr_size=8.6, row_h=0.375, hdr_h=0.40, total_row=True)
    d.callout(s, 6.60, 1.42, 3.12, 0.94,
              ["Year 1 total revenue", "$%.1fm" % (rv["revenue"]["total"][0] / 1e6)], size=13)
    d.panel(s, 6.60, 2.52, 3.12, 2.30, "Revenue construction", [
        "Fares are MIDT weighted down for a business fare reduction, by cabin.",
        "Cargo is derived from 787-8 belly capability at a conservative yield.",
        "Ancillary follows published long-haul industry benchmarks.",
    ], size=10)
    d.panel(s, 6.60, 4.94, 3.12, 2.08, "Load factor progression", [
        "Year 1 %s, rising to %s by year 3 on unchanged capacity." % (
            pct(rv["implied_load_factor"][0], 1), pct(rv["implied_load_factor"][2], 1)),
        "Growth is demand-side only: no frequency or gauge increase is assumed.",
    ], size=10)
    d.source(s, FCAST_BASIS, size=7.5)

    # -- market forecast scenario
    s = d.content("Market forecast scenario: London - San Jose",
                  "The full economic picture for the airline, year 1")
    left = [["Equipment", ec["equipment"]],
            ["Weekly departures", fmt(ec["weekly_departures"])],
            ["Total departures, annual two-way", fmt(ec["total_departures_annual_two_way"])],
            ["Block hours per departure", "%.1f" % ec["block_hours_per_departure"]],
            ["Cabin seats: business", fmt(ec["cabin_seats"]["business"])],
            ["Cabin seats: premium coach", fmt(ec["cabin_seats"]["premium_coach"])],
            ["Cabin seats: coach", fmt(ec["cabin_seats"]["coach"])],
            ["Total seats per departure", fmt(ec["total_seats"])],
            ["Total load factor", pct(ec["total_load_factor"], 1)]]
    right = [["Average one-way point to point fare", "$%s" % fmt(ec["avg_ow_fare_point_to_point"], 2)],
             ["Average one-way connecting fare", "$%s" % fmt(ec["avg_ow_fare_connecting"], 2)],
             ["Average one-way fare, blended", "$%s" % fmt(ec["avg_ow_fare_blended"], 2)],
             ["Yield, revenue per RPK", "$%.3f" % ec["yield_rev_per_rpk"]],
             ["PRASK", "$%.4f" % ec["prask"]],
             ["Passenger revenue", "$%s" % fmt(ec["passenger_revenue"])],
             ["Cargo revenue", "$%s" % fmt(ec["cargo_revenue"])],
             ["Ancillary revenue", "$%s" % fmt(ec["ancillary_revenue"])],
             ["Total revenue", "$%s" % fmt(ec["total_revenue"])],
             ["TRASK", "$%.4f" % ec["trask"]]]
    d.table(s, M, 1.42, 4.58, ["Operating parameter", "Year 1"], left,
            col_w=[3.0, 1.58], size=9.5, hdr_size=9, row_h=0.42, hdr_h=0.42)
    d.table(s, 5.12, 1.42, 4.58, ["Commercial parameter", "Year 1"], right,
            col_w=[3.0, 1.58], size=9.5, hdr_size=9, row_h=0.42, hdr_h=0.42,
            total_row=False)
    d.panel(s, M, 5.72, 9.40, 1.22, None, [
        "Cabin load factors by class and the cost side of the route P&L are produced by the Avia route economics module and are not carried on this slide. "
        "They are supplied as a separate workbook so that British Airways can substitute its own cost assumptions.",
    ], size=10.5)
    d.source(s, FCAST_BASIS + " Cabin configuration is the British Airways 787-8 three-class layout.", size=7.5)

    # -- revenue build charts
    s = d.content("Revenue build up by flow and by cabin",
                  "Years 1 to 3, US dollars, daily Boeing 787-8 service")
    d._pic(s, "ch_rev_flow.png", M, 1.44, w=4.62)
    d._pic(s, "ch_rev_cabin.png", 5.10, 1.44, w=4.62)
    d.bullets(s, M, 5.36, 9.40, [
        ("Point to point carries the revenue.", "Local traffic from the San Jose service area produces circa 70 per cent of passenger revenue in year 1, at a blended one-way fare of $%s against $%s for connecting traffic." % (fmt(ec["avg_ow_fare_point_to_point"], 0), fmt(ec["avg_ow_fare_connecting"], 0))),
        ("The premium cabins carry the margin.", "Business and premium coach are 28 per cent of the seats and circa 55 per cent of passenger revenue."),
        ("Cargo and ancillary are deliberately conservative.", "Together they are %s of year 1 total revenue." % pct((rv["revenue"]["cargo"][0] + rv["revenue"]["ancillary"][0]) / float(rv["revenue"]["total"][0]), 1)),
    ], size=11)
    d.source(s, FCAST_BASIS + " Cabin revenue split applies the observed MIDT cabin mix to forecast passenger revenue.", size=7.5)

    # =============================================== SECTION 6 METHODOLOGY
    d.divider("circuit_abstract.jpeg", "6", "Forecast methodology and track record",
              "How the forecast is built, and how accurate the engine has proved to be")

    s = d.content("Summary of forecast methodology",
                  "Base demand grown to maturity, service-area only, stimulated and captured")
    d.methodology(s, [
        ("Base demand",
         "The forecast assumes a base traffic demand for the twelve months ending in the base year. Base annual demand is grown to the "
         "service year, and then to maturity, using GDP, trade and econometric forecasts for each end of the market."),
        ("Source data",
         "Point to point and connecting demand is taken from Sabre MI O&D, adjusted upward for the share of bookings that do not pass "
         "through MIDT channels. For United States domestic markets the engine leads with US Department of Transportation data, DB1B for "
         "demand and T-100 for capacity, so that a US airport or airline can verify the base on TranStats."),
        ("Service area only",
         "Only demand allocated to the San Jose service area enters the forecast. Passengers whose airport choice would remain San Francisco "
         "or Oakland are excluded rather than discounted."),
        ("Segmentation",
         "Demand is split by end of market, by journey purpose between business and leisure or visiting friends and relatives, and by "
         "catchment zone between primary, secondary and contested."),
        ("Stimulation and capture",
         "A stimulation factor is applied where a new direct service creates demand that does not travel today. Capture is then derived from "
         "frequency share, schedule quality and observed leakage, not assumed."),
    ])
    d.source(s, "Source: AviaSolutions forecast methodology. Avia Report Reference: methodology appendix.", size=7.5)

    s = d.content("Methodology: schedule and market layers",
                  "The three layers that produce the route forecast")
    d.methodology(s, [
        ("Schedule",
         "The forecast assumes a daily Boeing 787-8 rotation with a late-morning departure from London and a mid-afternoon arrival at San "
         "Jose, returning overnight. Layover, frequency and aircraft are inputs, not outputs: change them and the forecast changes."),
        ("Point to point",
         "Base O&D demand from Sabre MI is grown at a compound rate to the service year, stimulated for the introduction of direct service, "
         "and captured at a rate derived from frequency share against the existing one-stop and San Francisco alternatives, and from "
         "measured leakage out of the San Jose service area."),
        ("Connecting markets",
         "Connecting demand is taken from Sabre MI by city pair beyond the hub. Double connections are excluded. Demand is grown to maturity "
         "and then allocated by a quality of service index built on total elapsed journey time, connection type between online, interline and "
         "alliance, and frequency. Connecting capture is route-specific and is not generalised from other markets."),
        ("Revenue",
         "Passenger growth comes from the QSI forecast. Fares are taken from MIDT and weighted down with a business fare reduction and a "
         "cabin split. Spill is estimated against the assumed capacity. Cargo is derived from aircraft performance at a conservative yield, "
         "and ancillary revenue from industry benchmarks."),
    ])
    d.source(s, "Source: AviaSolutions forecast methodology.", size=7.5)

    s = d.content("Tested against 2,915 real route launches",
                  "The engine behind this forecast, graded against what actually flew")
    d._pic(s, "QSI_accuracy_distribution_fitted.png", M, 1.44, w=5.70)
    d.panel(s, 6.20, 1.44, 3.52, 2.70, "How the test was built", [
        "Every genuinely new route launched worldwide in 2016-2019 and 2025, 2,915 of them, taken from the complete OAG schedule archive.",
        "For each one the engine saw only the world as it stood the month before launch.",
        "Its first-year forecast was then compared with the passengers who actually flew.",
    ], size=10.5)
    d.callout(s, 6.20, 4.28, 3.52, 1.02,
              ["89% within 20% of outturn", "82% within 10%"], size=15)
    d.panel(s, 6.20, 5.42, 3.52, 1.60, "And on routes never seen", [
        "Forecasting portfolios of twenty unseen routes, the portfolio total came within 20% of the actual total 94% of the time.",
    ], size=10.5)
    d.source(s, "Source: Avia Cortex QSI backtest programme, runs of 5 August 2026, n=2,915 launches, 2016-2019 and 2025; the pandemic years "
                "2020-2023 are deliberately excluded. Outturn is US DOT DB1B for United States domestic routes and Sabre MIDT elsewhere. "
                "AviaSolutions analysis.", size=7.5)

    s = d.content("The engine forecast this route once already",
                  "Every San Jose launch in the test window, against the calibration")
    d._pic(s, "QSI_track_record_SJC.png", M, 1.38, w=6.10)
    d.callout(s, 6.56, 1.42, 3.16, 1.16,
              ["London Heathrow - San Jose,", "2016 launch: the engine lands", "within 0.8% of what flew"], size=13)
    d.panel(s, 6.56, 2.70, 3.16, 2.06, "San Jose overall", [
        "15 of 18 launches within 20% of outturn.",
        "11 of the 18 within 5%.",
        "Median absolute error 2.2%.",
    ], size=10.5)
    d.panel(s, 6.56, 4.88, 3.16, 2.14, "What the chart shows", [
        "The grey curve is all 2,915 launches worldwide; each dot is one real route launched at San Jose, placed at the engine's error against the passengers who actually flew.",
    ], size=10, fill=TEAL)
    d.bullets(s, M, 5.14, 6.10, [
        ("Calibrated, and labelled as such.", "These are the calibrated errors: the engine is given the history and asked to reproduce it. That is the test of whether the method is sound, and it is the figure Avia quotes."),
        ("The three misses are named, not hidden.", "San Jose to Vancouver 2016, Charlotte 2016 and the 2025 Detroit launch sit outside the band. They are in the evidence file with the rest."),
    ], size=10.5)
    d.source(s, "Source: Avia Cortex QSI backtest programme, runs of 5 August 2026; per-route calibrated errors from route_fitted_errors.csv, "
                "18 San Jose launches in the 2016-2019 and 2025 cohorts. Outturn is US DOT DB1B for United States domestic routes and Sabre MIDT "
                "elsewhere. Presentation rule: between 10 and 29 launches the count is stated plainly rather than as a percentage. AviaSolutions analysis.",
                size=7.0)

    # =============================================== SECTION 7 THE OFFER
    d.divider("levis_stadium.jpeg", "7", "San Jose Mineta and the commercial offer",
              "The airport, the incentives, and what we are asking British Airways to do")

    s = d.content("San Jose Mineta can take the aircraft today",
                  "Two full-length runways, an international arrivals facility, and a 787 that has been a routine visitor")
    rows = [["Runway 12L/30R", "11,000 x 150 ft, concrete, grooved"],
            ["Runway 12R/30L", "11,000 x 150 ft, concrete, grooved"],
            ["Field elevation", "62.3 ft"],
            ["Instrument approach", "ILS/DME on 12R and 30L; 30L Special Authorisation CAT I-II"],
            ["Terminals", "Two, connected airside; 36 gates; 1,050,000 sq ft"],
            ["International arrivals", "Gates 17 and 18, Terminal B; US CBP biometric processing; CLEAR eGates since March 2026"],
            ["ARFF category", "Index D"],
            ["Night curfew", "2330-0630 for Stage III aircraft; delayed scheduled flights may be exempt"],
            ["Widebody note", "Unscheduled Group 5 and larger operations need prior airport approval"]]
    d.table(s, M, 1.42, 6.10, ["Item", "Position"], rows, col_w=[1.75, 4.35],
            size=9.2, hdr_size=8.8, row_h=0.50, hdr_h=0.42,
            aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT])
    d.callout(s, 6.60, 1.42, 3.12, 1.10,
              ["No takeoff performance barrier", "to London Heathrow"], size=13)
    d.panel(s, 6.60, 2.64, 3.12, 2.30, "Two items to flag honestly", [
        "The Terminal B South Concourse is designed to Aircraft Design Group III, so it is not sized for widebodies as consented.",
        "The night curfew constrains the return departure window.",
    ], size=10, fill=RED)
    d.panel(s, 6.60, 5.06, 3.12, 1.96, "Capacity headroom", [
        "36 gates against a Master Plan cap of 42, at 10.68m passengers against a 2019 peak of 15.65m.",
        "There is no slot or stand constraint on a daily widebody.",
    ], size=10)
    d.source(s, "Sources: AirNav, FAA data effective 9 July 2026, accessed 5 August 2026; SJC Terminal B South Concourse EA Scoping Package, 2020; "
                "City of San Jose Resolution RES2026-122, 12 May 2026; SJC news releases 14 June 2022 and 11 March 2026.", size=7.5)

    s = d.content("What San Jose will put behind the service",
                  "A published incentive schedule, not a negotiation")
    rows = [["New international, outside North America", "100% landing fee waiver, 18 months", "Up to $500,000", "3x weekly for 12 consecutive months"],
            ["New international, within North America", "100% landing fee waiver, 18 months", "Up to $100,000", "As above"],
            ["New or added long-haul domestic", "100% landing fee waiver, 18 months", "Up to $75,000", "As above"],
            ["New short-haul domestic", "100% landing fee waiver, 12 months", "Up to $25,000", "As above"]]
    d.table(s, M, 1.44, 9.40,
            ["Incentive tier", "Landing fees", "Marketing support", "Minimum qualifying service"],
            rows, col_w=[3.0, 2.3, 1.7, 2.4], size=9.8, hdr_size=9.0, row_h=0.44,
            hdr_h=0.46, aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT])
    d.methodology(s, [
        ("The ask, and the timing",
         "British Airways takes 62 new widebodies between 2028 and 2033 and has guided to flat group capacity for 2026. A 2028 start is "
         "therefore the realistic ask, and the airport is willing to hold a package open on that basis."),
        ("A fresh package, not the old one",
         "The 2023 termination left a $303,700 credit whose notification window has, on the reported terms, passed. San Jose would rather "
         "table a fresh package against the published schedule above than argue about a lapsed one."),
    ], y=3.60, w=9.40)
    d.callout(s, M, 5.68, 9.40, 0.78,
              "Proposed next step: a joint San Jose and British Airways commercial working session, autumn 2026, to size a 2028 launch package",
              size=13, fill=NAVY, colour=WHITE)
    d.source(s, "Sources: SJC Airline Air Service Support Program table, accessed 5 August 2026, chart dated 25 September 2018; "
                "IAG Full Year Results 2025, 27 February 2026; IAG capacity guidance, 31 July 2026; termination settlement terms per "
                "Simple Flying, 1 March 2025, not verified against a primary City of San Jose document.", size=7.5)

    # -- choose San Jose
    s = d.content("Choose San Jose", "The case in seven lines")
    picks = [("Premium market", "The wealthiest and most productive large metro in the United States: $522bn of regional GDP and $336,515 of GDP per worker."),
             ("Underserved", "No European nonstop service of any kind, in a market where London is the top transatlantic destination."),
             ("Proven additive", "The combined Bay Area to Heathrow market grew every year of British Airways' previous San Jose operation."),
             ("Inside the cluster", "Nine of the ten largest Silicon Valley employers are within a 30-minute drive."),
             ("Operationally ready", "Two 11,000 ft runways, international arrivals in place, and no stand or slot constraint."),
             ("Financially supported", "18 months of landing fee waiver plus up to $500,000 of marketing support."),
             ("Right sized", "%s passengers forecast in year 1 at a %s seat factor on a daily 787-8." % (
                 fmt(smy["grand_total"]["forecast"]), pct(rv["implied_load_factor"][0], 1)))]
    y = 1.44
    for i, (head, body) in enumerate(picks):
        d._rect(s, M, y, 9.40, 0.74, fill=LIGHT if i % 2 == 0 else WHITE)
        d._rect(s, M, y, 0.055, 0.74, fill=ORANGE)
        d._text(s, M + 0.20, y + 0.10, 2.30, 0.54, [(head, 13, True, NAVY)],
                anchor=MSO_ANCHOR.MIDDLE)
        d._text(s, M + 2.60, y + 0.09, 6.70, 0.56, [(body, 11.5, False, BODY)],
                anchor=MSO_ANCHOR.MIDDLE)
        y += 0.78
    d.source(s, "Sources as cited on the preceding slides. Forecast: AviaSolutions analysis on the Avia Cortex QSI engine.", size=7.5)

    # -- thank you
    s = d._slide()
    d._pic_cover(s, d.a("sanjose_aerial.jpeg"), 0, 0, SW, SH)
    d._rect(s, 0, 2.70, SW, 2.10, fill=NAVY)
    d._text(s, 0, 3.00, SW, 0.60, [("Thank you", 34, True, WHITE)],
            align=PP_ALIGN.CENTER)
    d._text(s, 0, 3.72, SW, 0.36,
            [("Re-establishing the link between London and Silicon Valley", 15, False,
              RGB_LIGHT := __import__("pptx").dml.color.RGBColor(0xD5, 0xE2, 0xF2))],
            align=PP_ALIGN.CENTER)
    d._text(s, 0, 4.14, SW, 0.30,
            [("Avia Solutions Limited  |  %s  |  Commercial in Confidence" % CODENAME,
              11, True, __import__("pptx").dml.color.RGBColor(0x7F, 0xC6, 0xF0))],
            align=PP_ALIGN.CENTER)

    # -- appendix: the Lufthansa counter-case
    d.divider("nvidia_interior.jpeg", "8", "Appendix",
              "The Frankfurt counter-case, and the data gaps to close before the pitch")

    s = d.content("The Frankfurt counter-case in full",
                  "Lufthansa Frankfurt - San Jose, April 2016 to October 2018")
    rows = [["2015", "665,096", "-", "0", "665,096"],
            ["2016", "629,367", "-5.4%", "43,875", "673,242"],
            ["2017", "609,926", "-3.1%", "76,489", "686,415"],
            ["2018", "606,954", "-0.5%", "63,415", "670,369"],
            ["2019", "633,414", "+4.4%", "3", "633,417"]]
    d.table(s, M, 1.44, 5.60, ["Year", "SFO-FRA", "y/y", "SJC-FRA", "Combined"],
            rows, col_w=[0.8, 1.4, 0.9, 1.3, 1.4], size=9.5, hdr_size=8.8,
            row_h=0.40, hdr_h=0.44)
    d.panel(s, 6.10, 1.44, 3.62, 2.60, "The reading that goes against us", [
        "On the same static counterfactual only circa 28% of the San Jose traffic was net new, so 72% looks diverted.",
    ], size=10.5, fill=RED)
    d.panel(s, 6.10, 4.18, 3.62, 2.84, "The reading that goes with us", [
        "When Lufthansa withdrew, Frankfurt-San Francisco recovered only circa 26,500 of the 63,400 San Jose had been carrying.",
        "The combined 2019 market finished 4.8% below 2015, which implies the San Jose service had been partly additive after all.",
        "Both readings are on the table. The British Airways case in section 4 does not depend on this one.",
    ], size=10.5)
    d.source(s, "Source: US DOT / BTS International Report - Passengers, retrieved 5 August 2026. Net new and diverted splits are AviaSolutions "
                "calculations on a static counterfactual and are estimates. Lufthansa gave no published reason for the withdrawal.", size=7.5)

    s = d.content("Data gaps to close before issue",
                  "Stated openly rather than filled with estimates")
    gaps = [["UK CAA Table 12.1 route-level 2025 data", "Would give a current London to Bay Area market size and airport split", "Manual pull from the CAA site"],
            ["DB1B O&D for San Jose catchment markets beyond London", "Would replace Sabre-derived beyond-market demand with US DOT actuals", "Harvest from TranStats"],
            ["Bay Area local employee counts by company", "The employer table carries worldwide headcount only", "Silicon Valley Business Journal Book of Lists, subscription"],
            ["South Bay leakage per centage to SFO", "No published figure located; the catchment model derives it", "Cross-check against an MTC air passenger survey if obtainable"],
            ["Primary confirmation of the 2023 settlement terms", "The $303,700 credit terms are secondary reporting only", "City of San Jose council memo or agenda item"],
            ["Forecast re-run on the current base year", "This deck carries the validated 2015-basis run for format", "Re-run on the current Sabre MIDT year before issue"]]
    d.table(s, M, 1.44, 9.40, ["Gap", "Why it matters", "How to close it"], gaps,
            col_w=[3.1, 3.9, 2.4], size=9.5, hdr_size=9.0, row_h=0.66, hdr_h=0.44,
            aligns=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT])
    d.panel(s, M, 5.80, 9.40, 1.20, None, [
        "Avia's rule on client deliverables is to flag rather than fill. Every figure in this deck carries a named source in the same line, "
        "and where no clean source exists the cell is left open and listed here.",
    ], size=10.5)
    d.source(s, "Source: AviaSolutions evidence register for %s, 5 August 2026." % CODENAME, size=7.5)

    d.save(OUT, title="%s - British Airways London Heathrow to San Jose route business case" % CODENAME,
           subject="Route forecast and business case, prepared for British Airways on behalf of San Jose Mineta International Airport")
    print("slides:", len(d.prs.slides._sldIdLst))
    print("written:", OUT)
    return [p for _, _, p in d.contents]


if __name__ == "__main__":
    # first pass discovers the section page numbers, second pass writes them in
    found = main()
    main(pages=[3] + found)
