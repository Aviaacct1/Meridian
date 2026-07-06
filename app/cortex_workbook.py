#!/usr/bin/env python3
"""
Avia Cortex - detailed route workbook (built straight from the calibrated forecast).
====================================================================================
build_workbook(out_path, fc, meta) writes the client-ready Excel with the full tables that
sit behind the deck: the forecast breakdown, the connecting-feed detail each way (PDEW), the
catchment split, the turnaround P&L line items, and an assumptions / methodology log. It reads
the calibrated_forecast() dict directly, so every number matches the portal, and needs nothing
from the old pipeline. Author is set to Avia Solutions.

  fc   = the calibrated_forecast() output dict (ok, origin, dest, demand, capacity, catchment,
         economics{raw}, distance_nm, block_min, week, year)
  meta = dict(airline_name, analyst, date, plan_lf, capture_basis, econ_fare)
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

AVIA = "1F3864"; MID = "2F6BF0"; LIGHT = "EAF0FE"; GREENF = "E6F6EF"
HDR = PatternFill("solid", fgColor=AVIA)
SEC = PatternFill("solid", fgColor="4472C4")
LFILL = PatternFill("solid", fgColor=LIGHT)
TOTF = PatternFill("solid", fgColor="D6E4F0")
WHITE = Font(name="Arial", bold=True, color="FFFFFF", size=10)
TITLE = Font(name="Arial", bold=True, color=AVIA, size=15)
BOLD = Font(name="Arial", bold=True, size=10)
NORM = Font(name="Arial", size=10)
NOTE = Font(name="Arial", size=9, italic=True, color="666666")
TOTF_FONT = Font(name="Arial", bold=True, color=AVIA, size=11)
CTR = Alignment(horizontal="center", vertical="center", wrap_text=True)
LFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
LFT_NW = Alignment(horizontal="left", vertical="center", wrap_text=False)
RGT = Alignment(horizontal="right", vertical="center")
THIN = Border(*(Side("thin", color="C9D3E4"),) * 4)


def _c(ws, r, c, v=None, font=NORM, fill=None, fmt=None, align=CTR, border=THIN):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font = font; cell.alignment = align
    cell.border = border if border is not None else Border()  # a real (empty) border, never None, so merge_cells can read its sides
    if fill: cell.fill = fill
    if fmt: cell.number_format = fmt
    return cell


def _hdr(ws, r, headers, widths=None):
    for i, h in enumerate(headers, 1):
        _c(ws, r, i, h, font=WHITE, fill=HDR)
    if widths:
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w


def _sec(ws, r, text, span):
    for i in range(1, span + 1):
        _c(ws, r, i, text if i == 1 else None, font=WHITE, fill=SEC, align=LFT_NW)
    if span > 1:
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=span)


def _title(ws, text, sub="", span=6):
    _c(ws, 1, 1, text, font=TITLE, align=LFT_NW, border=None)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=span)
    if sub:
        _c(ws, 2, 1, sub, font=NOTE, align=LFT_NW, border=None)
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=span)


def build_workbook(out_path, fc, meta=None):
    meta = meta or {}
    o = fc["origin"]; d = fc["dest"]; dem = fc["demand"]; cap = fc["capacity"]
    ec = fc.get("economics") or {}; raw = ec.get("raw") or {}
    home = fc["catchment"]["home"]; nm = fc["catchment"]["names"]; sh = fc["catchment"]["observed_share"]
    airline = meta.get("airline_name") or fc.get("airline") or "New entrant"
    n0 = lambda v: float(v or 0)
    wb = openpyxl.Workbook()

    # ---- 1. Cover -----------------------------------------------------------
    ws = wb.active; ws.title = "Cover"
    ws.column_dimensions["A"].width = 34; ws.column_dimensions["B"].width = 40
    _title(ws, f'{o["city"]} to {d["city"]}  ({home}-{d["iata"]})', "Avia Cortex route forecast - detailed workbook")
    r = 4
    blocks = [
        ("ROUTE", [("Origin", f'{o["city"]} ({home})'), ("Destination", f'{d["city"]} ({d["iata"]})'),
                   ("Country", f'{o.get("country","")} to {d.get("country","")}'),
                   ("Sector", f'{fc.get("distance_nm",0):,} nm'), ("Block time", f'{fc.get("block_min",0)} min')]),
        ("SERVICE", [("Airline", airline), ("Carrier type", fc.get("carrier_type","")),
                     ("Aircraft", cap.get("aircraft","")), ("Seats", ec.get("seats","")),
                     ("Frequency", f'{cap.get("freq","")}x/week')]),
        ("FORECAST (each way / year)", [("Point to point", round(n0(dem.get("captured")))),
                     ("Connecting behind " + home, round(n0(dem.get("feed_behind")))),
                     ("Connecting beyond " + d["iata"], round(n0(dem.get("feed_beyond")))),
                     ("Total forecast", round(n0(dem.get("total")))),
                     ("Planned load factor", n0(cap.get("load"))),
                     ("Passengers/day each way", dem.get("pdew_total"))]),
        ("BASIS", [("OAG schedule week", fc.get("week","")), ("Sabre O&D year", fc.get("year","")),
                   ("Analyst", meta.get("analyst","Avia Solutions")), ("Date", meta.get("date",""))]),
    ]
    for title, rows in blocks:
        _sec(ws, r, title, 2); r += 1
        for k, v in rows:
            _c(ws, r, 1, k, font=BOLD, align=LFT)
            if isinstance(v, float) and 0 < v < 1:
                _c(ws, r, 2, v, fmt="0.0%", align=RGT)
            elif isinstance(v, (int, float)):
                _c(ws, r, 2, v, fmt="#,##0", align=RGT)
            else:
                _c(ws, r, 2, v, align=RGT)
            r += 1
        r += 1

    # ---- 2. Traffic forecast (Avia gold-standard layout) -------------------
    ws = wb.create_sheet("Forecast")
    _title(ws, "Traffic forecast", "each way per year; connecting rows show the captured feed")
    _hdr(ws, 4, ["Market", "Base demand (000s)", "Growth", "Grown demand (000s)", "Stimulation",
                 "Stimulated demand (000s)", "Capture rate", "Forecast (000s)", "PTEW"],
         [30, 13, 9, 13, 11, 15, 11, 12, 9])
    cap_share = n0(dem.get("qsi_share")); stim = n0(dem.get("stimulation")) or 1.0
    natural = n0(dem.get("natural")); p2p = n0(dem.get("captured"))
    behind = n0(dem.get("feed_behind")); beyond = n0(dem.get("feed_beyond")); tot = n0(dem.get("total"))
    freq = n0(cap.get("freq")) or 7.0
    k = lambda x: round(x / 1000.0, 1)
    ptew = lambda x: round(x / (freq * 52.0)) if freq else 0
    r = 5
    _c(ws, r, 1, "Total point to point", font=BOLD, align=LFT)
    _c(ws, r, 2, k(natural), fmt="#,##0.0", align=RGT); _c(ws, r, 3, 0, fmt="0%", align=RGT)
    _c(ws, r, 4, k(natural), fmt="#,##0.0", align=RGT); _c(ws, r, 5, round(stim, 2), fmt="0.00", align=RGT)
    _c(ws, r, 6, k(natural * stim), fmt="#,##0.0", align=RGT); _c(ws, r, 7, cap_share, fmt="0.0%", align=RGT)
    _c(ws, r, 8, k(p2p), fmt="#,##0.0", align=RGT); _c(ws, r, 9, ptew(p2p), fmt="#,##0", align=RGT)
    r += 1
    for label, val, cbase in [(f"Total connecting behind {home}", behind, n0(dem.get("feed_behind_base"))),
                              (f"Total connecting beyond {d['iata']}", beyond, n0(dem.get("feed_beyond_base")))]:
        _c(ws, r, 1, label, font=BOLD, align=LFT)
        _c(ws, r, 2, k(cbase) if cbase else "-", fmt="#,##0.0", align=RGT)
        _c(ws, r, 3, 0, fmt="0%", align=RGT)
        _c(ws, r, 4, k(cbase) if cbase else "-", fmt="#,##0.0", align=RGT)
        _c(ws, r, 5, 1.00, fmt="0.00", align=RGT)
        _c(ws, r, 6, k(cbase) if cbase else "-", fmt="#,##0.0", align=RGT)
        _c(ws, r, 7, (val / cbase) if cbase else "-", fmt="0.0%", align=RGT)
        _c(ws, r, 8, k(val), fmt="#,##0.0", align=RGT); _c(ws, r, 9, ptew(val), fmt="#,##0", align=RGT)
        r += 1
    _c(ws, r, 1, "GRAND TOTAL", font=TOTF_FONT, fill=TOTF, align=LFT)
    for cc in range(2, 8):
        _c(ws, r, cc, None, fill=TOTF)
    _c(ws, r, 8, k(tot), font=TOTF_FONT, fill=TOTF, fmt="#,##0.0", align=RGT)
    _c(ws, r, 9, ptew(tot), font=TOTF_FONT, fill=TOTF, fmt="#,##0", align=RGT)
    _c(ws, r + 2, 1, "Base demand is the addressable each-way O&D market from Sabre in the origin catchment. "
                     "Point-to-point forecast = stimulated demand x capture rate, capacity-bounded. Connecting "
                     "rows show the captured feed each way. PTEW = passengers per departure each way.",
       font=NOTE, align=LFT, border=None)

    # ---- 3. Connecting feed detail (base demand, share, forecast, PDEW) -----
    ws = wb.create_sheet("Connecting feed")
    _title(ws, "Connecting feed detail", "connecting markets each way: base O&D demand, captured share, forecast, PDEW")
    r = 4
    for label, key in [(f"Connecting at {home} (behind the origin)", "behind_pdew"),
                       (f"Connecting at {d['iata']} (beyond the destination)", "beyond_pdew")]:
        _sec(ws, r, label, 8); r += 1
        _hdr(ws, r, ["Nr", "Code", "City", "Country", "Annual demand", "Share", "Annual forecast", "PDEW"],
             [6, 10, 24, 20, 15, 10, 15, 9]); r += 1
        lst = dem.get(key) or []; sub_base = 0.0; sub_fc = 0.0
        for i, row in enumerate(lst, 1):
            base = n0(row.get("base")); shr = n0(row.get("share"))
            fcv = n0(row.get("forecast")) or (n0(row.get("pdew")) * 365.0); pdv = n0(row.get("pdew"))
            if fcv <= 0 and pdv <= 0:
                continue
            sub_base += base; sub_fc += fcv
            _c(ws, r, 1, i, align=CTR); _c(ws, r, 2, row.get("code"), align=CTR)
            _c(ws, r, 3, row.get("name"), align=LFT); _c(ws, r, 4, row.get("country") or "", align=LFT)
            _c(ws, r, 5, round(base) if base else "-", fmt="#,##0", align=RGT)
            _c(ws, r, 6, shr if base else "-", fmt="0.0%", align=RGT)
            _c(ws, r, 7, round(fcv), fmt="#,##0", align=RGT); _c(ws, r, 8, round(pdv, 1), fmt="#,##0.0", align=RGT)
            r += 1
        _c(ws, r, 1, "Total", font=BOLD, fill=TOTF, align=LFT)
        for cc in (2, 3, 4, 6, 8):
            _c(ws, r, cc, None, fill=TOTF)
        _c(ws, r, 5, round(sub_base) if sub_base else "-", font=BOLD, fill=TOTF, fmt="#,##0", align=RGT)
        _c(ws, r, 7, round(sub_fc), font=BOLD, fill=TOTF, fmt="#,##0", align=RGT); r += 2

    # ---- 3b. Schedule and capacity ----------------------------------------
    ws = wb.create_sheet("Schedule")
    _title(ws, "Schedule and capacity", f'{cap.get("aircraft","")} at {int(freq)}x/week (indicative times)')
    _hdr(ws, 4, ["Sector", "Dep", "Arr", "Op days/week", "Aircraft", "Seats", "Annual seats", "Annual pax", "Seat factor"],
         [13, 9, 9, 13, 12, 9, 14, 13, 11])
    sched = fc.get("schedule") or {}
    seats = n0(ec.get("seats")); load = n0(cap.get("load"))
    ann_seats_dir = seats * freq * 52.0
    r = 5
    for leg in ("outbound", "inbound"):
        s = sched.get(leg) or {}
        sector = s.get("sector") or (f'{home}-{d["iata"]}' if leg == "outbound" else f'{d["iata"]}-{home}')
        _c(ws, r, 1, sector, font=BOLD, align=LFT); _c(ws, r, 2, s.get("dep") or "-", align=CTR)
        _c(ws, r, 3, s.get("arr") or "-", align=CTR); _c(ws, r, 4, int(freq), align=RGT)
        _c(ws, r, 5, cap.get("aircraft", ""), align=CTR); _c(ws, r, 6, round(seats), fmt="#,##0", align=RGT)
        _c(ws, r, 7, round(ann_seats_dir), fmt="#,##0", align=RGT); _c(ws, r, 8, round(tot), fmt="#,##0", align=RGT)
        _c(ws, r, 9, load, fmt="0.0%", align=RGT); r += 1
    _c(ws, r, 1, "Total", font=BOLD, fill=TOTF, align=LFT)
    for cc in (2, 3, 4, 5, 6):
        _c(ws, r, cc, None, fill=TOTF)
    _c(ws, r, 7, round(ann_seats_dir * 2), font=BOLD, fill=TOTF, fmt="#,##0", align=RGT)
    _c(ws, r, 8, round(tot * 2), font=BOLD, fill=TOTF, fmt="#,##0", align=RGT)
    _c(ws, r, 9, load, font=BOLD, fill=TOTF, fmt="0.0%", align=RGT)
    _c(ws, r + 2, 1, "Departure and arrival are indicative local times derived from block time and timezone; "
                     "not curfew- or slot-optimised. Annual seats = seats x frequency x 52, each direction; "
                     "annual pax is the forecast each way; seat factor is the planned load.", font=NOTE, align=LFT, border=None)

    # ---- 4. Catchment split ------------------------------------------------
    ws = wb.create_sheet("Catchment")
    _title(ws, "Catchment airport split", "how the origin catchment's demand splits across competing airports today")
    _hdr(ws, 4, ["Airport", "Share of catchment"], [40, 18])
    r = 5
    for c, v in sorted(sh.items(), key=lambda kv: -kv[1]):
        lbl = nm.get(c) or c
        _c(ws, r, 1, lbl + ("  (this route's origin)" if c == home else ""),
           font=(BOLD if c == home else NORM), fill=(GREENF and PatternFill("solid", fgColor=GREENF)) if c == home else None, align=LFT)
        _c(ws, r, 2, round(n0(v), 4), fmt="0.0%", align=RGT); r += 1
    cb = meta.get("capture_basis", "modelled from drive time and competing service")
    _c(ws, r + 1, 1, f"Assumed capture with this route's own nonstop: {cap_share*100:.1f}%  ({cb}).",
       font=NOTE, align=LFT, border=None)

    # ---- 5. Route economics (turnaround P&L) -------------------------------
    ws = wb.create_sheet("Economics")
    _title(ws, "Route economics", f'turnaround P&L on the {cap.get("aircraft","")}, one rotation out and back')
    _hdr(ws, 4, ["Line item", "Per rotation ($)"], [40, 20]); r = 5
    def prow(k, v, bold=False, fill=None):
        nonlocal r
        _c(ws, r, 1, k, font=(BOLD if bold else NORM), fill=fill, align=LFT)
        _c(ws, r, 2, round(n0(v)), font=(BOLD if bold else NORM), fill=fill, fmt="#,##0", align=RGT); r += 1
    _sec(ws, r, "REVENUE", 2); r += 1
    prow("Passenger revenue (net)", raw.get("net_rev")); prow("Cargo", raw.get("cargo_rev"))
    prow("Charges recovery", raw.get("charges_recovery")); prow("Gross revenue", raw.get("gross_rev"), True, LFILL)
    _sec(ws, r, "OPERATING COST", 2); r += 1
    for k, key in [("Fuel", "fuel"), ("Maintenance", "maintenance"), ("Crew", "crew"), ("Ownership", "ownership"),
                   ("Insurance", "insurance"), ("Landing", "landing"), ("Passenger charges", "per_pax"),
                   ("Ground handling", "handling"), ("En-route navigation", "nav"), ("Catering", "catering"),
                   ("Admin", "admin"), ("Sales", "sales")]:
        prow(k, -abs(n0(raw.get(key))))
    prow("Total operating cost", -abs(n0(raw.get("total_cost"))), True, LFILL)
    prow("Operating profit per rotation", raw.get("profit"), True, TOTF)
    r += 1
    _sec(ws, r, "SUMMARY", 2); r += 1
    for k, v, fmt in [("Operating margin", n0(raw.get("margin")), "0.0%"),
                      ("Breakeven load factor", n0(raw.get("breakeven_lf")), "0.0%"),
                      ("Passengers per rotation", n0(raw.get("pax_turn")), "#,##0"),
                      ("Annual profit", n0(ec.get("annual_profit")), "#,##0"),
                      ("Aircraft required", ec.get("aircraft_required") or 0, "0.00")]:
        _c(ws, r, 1, k, font=BOLD, align=LFT); _c(ws, r, 2, v, fmt=fmt, align=RGT); r += 1

    # ---- 6. Assumptions & methodology --------------------------------------
    ws = wb.create_sheet("Assumptions")
    _title(ws, "Assumptions and methodology", "every key parameter behind this forecast")
    _hdr(ws, 4, ["Parameter", "Value", "Basis"], [30, 20, 60]); r = 5
    A = [
        ("Addressable market", f'{round(n0(dem.get("natural"))):,} each way/yr', "Sabre point-of-origin O&D in the origin catchment"),
        ("Origin QSI capture", f'{cap_share*100:.1f}%', meta.get("capture_basis", "modelled from drive time and competing service")),
        ("Coverage gross-up", f'x{n0(dem.get("coverage_gross_up")) or 1:.2f}', "uplift from surveyed to full O&D coverage"),
        ("Stimulation", f'x{stim:.2f}', "new nonstop demand uplift by carrier type"),
        ("Connecting feed", f'behind {round(behind):,}, beyond {round(beyond):,}', "alliance-weighted, circuity-screened onward O&D"),
        ("Planned load factor", f'{n0(cap.get("load"))*100:.0f}%', f'cap {n0(meta.get("plan_lf") or cap.get("load"))*100:.0f}%'),
        ("Economy fare (one way)", f'${round(n0(ec.get("econ_fare"))):,}', "Sabre-implied / distance floor"),
        ("Aircraft", cap.get("aircraft",""), "seats and burn from validated type economics"),
        ("Maintenance basis", raw.get("maint_basis",""), "sector-aware Airbus reserves"),
        ("Ownership basis", raw.get("own_basis",""), "blended owned/leased cost of capital by type and age"),
    ]
    for k, v, b in A:
        _c(ws, r, 1, k, font=BOLD, align=LFT); _c(ws, r, 2, v, align=RGT); _c(ws, r, 3, b, align=LFT); r += 1
    r += 1
    _sec(ws, r, "METHODOLOGY", 3); r += 1
    method = ("1. Catchment: the resident population within drive time of the origin, from GeoNames and "
              "least-cost road times.  2. Market: measured Sabre O&D each way in that catchment.  3. Capture: "
              "the QSI + access share the new nonstop takes from competing airports and airlines; measured "
              "survey/mobility data overrides the model where held.  4. Stimulation: uplift for the new nonstop.  "
              "5. Connecting feed: onward O&D behind the origin and beyond the destination on the chosen "
              "airline, alliance-weighted and circuity-screened.  6. Capacity cap: demand bounded by the "
              "aircraft and frequency at the planned load factor.  7. Economics: turnaround and annual P&L on "
              "validated type costs.  Indicative central estimate, for directional guidance.")
    _c(ws, r, 1, method, font=NORM, align=LFT); ws.merge_cells(start_row=r, start_column=1, end_row=r + 6, end_column=3)
    ws.row_dimensions[r].height = 120

    cp = wb.properties
    cp.creator = "Avia Solutions"; cp.lastModifiedBy = "Avia Solutions"
    cp.title = f'{o["city"]} to {d["city"]} route workbook'
    wb.save(out_path)
    return out_path
