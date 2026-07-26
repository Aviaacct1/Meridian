#!/usr/bin/env python3
"""
Avia Cortex - the Methodology page (John, 4 Jul 2026): how a forecast is built, explained so a
lay person can follow it, with a BRIDGE (waterfall) chart tied to the last forecast run on the
dashboard - each element of the build shown with its weight in the final number.

Server-rendered like track_record.py (no client-side JS to break on iPads). The bridge reads
the forecast payload the engine already returns (natural market, capture share, coverage
gross-up, stimulation, behind/beyond feed, capacity cap) so nothing here recomputes anything:
the page shows exactly what the engine did, which is the point - transparency as product.
Pairs with Track record: this page says WHAT we do, that one shows HOW WELL it does.

Offline test:  py -3.12 methodology_page.py > methodology_preview.html
"""
import html as _html

# ---- The Observatory palette (restyle) ----
INK, BRASS, BRASSD, SIGNAL = "#0F1B28", "#D4A249", "#A97C33", "#CE3B2A"
PAPER, SCREEN, LINE = "#F6F3EC", "#FAF8F3", "#E2DCCC"
BODY, INKTX = "#3A444E", "#26313B"
NAVY, ACCENT, MUT, BG = INK, BRASS, "#6E6A5E", SCREEN
GREEN, RED = "#5F8D7A", "#A9553F"   # waterfall: up = verdigris (adds), down = oxblood (reduces)
SERIF, SANS, MONO = "'Newsreader',Georgia,serif", "'Inter',system-ui,sans-serif", "'IBM Plex Mono',monospace"
FONT_LINK = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
  '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
  '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
  'family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;0,6..72,500;1,6..72,400'
  '&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">')

STEPS = [
    ("1", "Measure the whole market",
     "We start with every passenger already flying between the two catchment areas, however "
     "they route today - nonstop, one-stop, via any hub - from global booking (GDS) data. "
     "This is a measured number, not an estimate."),
    ("2", "Win a share of it",
     "A new nonstop competes with every existing way to make the trip. Each alternative is "
     "scored the way booking screens rank them - total journey time, schedule frequency, "
     "airline and alliance - the industry QSI method, and the new flight takes its fair share. "
     "Drive time to each competing airport decides which travellers are really in play."),
    ("3", "Correct for what bookings miss",
     "Booking data does not see every ticket (airline websites, package holidays). We gross up "
     "by a factor measured against airports' own passenger counts - never guessed."),
    ("4", "New-service stimulation",
     "A new nonstop grows its market: journeys that were too awkward or expensive before now "
     "happen. The factor comes from what actually happened on hundreds of launched routes, and "
     "it differs by airline type - a low-cost entrant stimulates more than a network carrier."),
    ("5", "Add connecting passengers",
     "Passengers connect ONTO the flight at both ends: from cities behind the origin, and "
     "onwards beyond the destination. Every possible connection is scored for quality - legal "
     "connection time, total journey, same airline or alliance - and the flight wins a share "
     "of each connecting market, which is why departure time changes the answer."),
    ("6", "Fit it to the aircraft",
     "Demand is then capped by what the proposed aircraft and frequency can actually carry at "
     "an achievable load factor - including whether the runway lets that aircraft take off at "
     "full weight (see the airfield check). What the metal cannot carry, the forecast does not "
     "claim."),
]


def _fmt(n):
    return f"{n:,.0f}"


def _bridge_svg(bars):
    """Waterfall: bars = [(label, sub, value, kind)] where kind in start/down/up/total and
    value is the SIGNED step (start/total = absolute level)."""
    W, H = 980, 400
    padl, padr, padt, padb = 60, 20, 34, 92
    n = len(bars)
    bw = (W - padl - padr) / n
    # running levels
    levels, run = [], 0.0
    for label, sub, v, kind in bars:
        if kind in ("start", "total"):
            levels.append((0.0, v)); run = v
        elif kind == "up":
            levels.append((run, run + v)); run += v
        else:
            levels.append((run + v, run)); run += v      # v negative
    top = max(hi for _lo, hi in levels) or 1.0
    sy = (H - padt - padb) / top
    y = lambda v: H - padb - v * sy
    L0, R0, T0, B0 = padl, W - padr, padt, H - padb
    out = [f'<svg viewBox="0 0 {W} {H}" style="width:100%;max-width:{W}px" font-family="{SANS}">']
    # registration corner ticks (Observatory signature)
    out.append(f'<g stroke="{INK}" stroke-width="1" fill="none">'
               f'<path d="M{L0} {T0} h10 M{L0} {T0} v10"/><path d="M{R0} {T0} h-10 M{R0} {T0} v10"/>'
               f'<path d="M{L0} {B0} h10 M{L0} {B0} v-10"/><path d="M{R0} {B0} h-10 M{R0} {B0} v-10"/></g>')
    out.append(f'<line x1="{padl}" y1="{y(0)}" x2="{W-padr}" y2="{y(0)}" stroke="{INK}" stroke-width="1.2"/>')
    prev_end = None
    for i, ((label, sub, v, kind), (lo, hi)) in enumerate(zip(bars, levels)):
        x = padl + i * bw + 6
        w = bw - 12
        col = {"start": INK, "total": BRASS, "up": GREEN, "down": RED}[kind]
        out.append(f'<rect x="{x:.0f}" y="{y(hi):.0f}" width="{w:.0f}" '
                   f'height="{max(2, (hi-lo)*sy):.0f}" fill="{col}"/>')
        if prev_end is not None:                          # connector
            out.append(f'<line x1="{x-6:.0f}" y1="{y(prev_end):.0f}" x2="{x:.0f}" '
                       f'y2="{y(prev_end):.0f}" stroke="{MUT}" stroke-dasharray="3 3" opacity="0.7"/>')
        prev_end = hi if kind in ("start", "up", "total") else lo
        val = hi if kind in ("start", "total") else abs(v)
        sign = "" if kind in ("start", "total") else ("+" if kind == "up" else "−")
        out.append(f'<text x="{x+w/2:.0f}" y="{y(hi)-7:.0f}" text-anchor="middle" font-size="12.5" '
                   f'font-family="{SERIF}" fill="{INK}">{sign}{_fmt(val)}</text>')
        out.append(f'<text x="{x+w/2:.0f}" y="{H-padb+18}" text-anchor="middle" font-size="10.5" '
                   f'font-weight="600" letter-spacing="0.04em" fill="{INK}">{label}</text>')
        out.append(f'<text x="{x+w/2:.0f}" y="{H-padb+33}" text-anchor="middle" font-size="9.5" '
                   f'fill="{MUT}">{sub}</text>')
    out.append("</svg>")
    return "".join(out)


def _bridge_from_fc(fc):
    dem = fc.get("demand") or {}
    cap = fc.get("capacity") or {}
    natural = float(dem.get("natural") or 0)
    share = float(dem.get("qsi_share") or 0)
    cov = float(dem.get("coverage_gross_up") or 1)
    stim = float(dem.get("stimulation") or 1)
    captured = float(dem.get("captured") or 0)
    fb = float(dem.get("feed_behind") or 0)
    fy = float(dem.get("feed_beyond") or 0)
    total = float(dem.get("total") or (captured + fb + fy))
    carried = float(cap.get("carried") or total)
    m_share = natural * share
    m_cov = m_share * cov
    bars = [
        ("Measured market", "all routings, booking data", natural, "start"),
        ("Capture share", f"{share*100:.1f}% by schedule quality", -(natural - m_share), "down"),
        ("Coverage", f"x{cov:.2f} measured gross-up", m_cov - m_share, "up" if cov >= 1 else "down"),
        ("Stimulation", f"x{stim:.2f} new-service growth", captured - m_cov, "up" if captured >= m_cov else "down"),
        ("Feed behind", "connections at the origin", fb, "up"),
        ("Feed beyond", "connections past the destination", fy, "up"),
    ]
    if carried < total - 0.5:
        bars.append(("Aircraft cap", "beyond seats x frequency", -(total - carried), "down"))
    bars.append(("Forecast", "carried, each way / year", carried, "total"))
    return bars


def _expert_section(fc):
    """The granular engine-room view for expert users: every stage, every assumption applied to
    THIS run, tagged by provenance. IP rule (John, 4 Jul 2026): route-specific values are shown
    in full; global calibrated constants and functional forms are described by provenance and
    validation, never by value - the parameter vector IS the IP, the transparency is not."""
    esc = _html.escape
    dem = fc.get("demand") or {}
    cap = fc.get("capacity") or {}
    ec = (fc.get("economics") or {})
    raw = ec.get("raw") or {}
    af = fc.get("airfield") or {}
    cat = fc.get("catchment") or {}
    n_comp = len((cat.get("observed_share") or {}))
    f = lambda n: f"{float(n or 0):,.0f}"

    def rows(items):
        out = []
        for label, val, tag, note in items:
            out.append(f'<tr><td>{esc(label)}</td><td class="v">{val}</td>'
                       f'<td><span class="tag {tag}">{tag}</span></td>'
                       f'<td class="nt">{esc(note)}</td></tr>')
        return "".join(out)

    stages = [
        ("A &middot; Base demand and data sources", [
            ("Catchment O&D market, each way/yr", f(dem.get("natural")), "measured",
             "Sabre GDS bookings, all routings, both catchments; the season/week shown on the dashboard"),
            ("Competing airports in the choice set", str(n_comp), "measured",
             "drive-time catchment; water boundaries respected for island airports"),
            ("Sector distance", f"{f(float(fc.get('distance_nm') or 0) * 1.852)} km", "measured",
             "great-circle; block time and fuel derive from it"),
        ]),
        ("B &middot; Capture (the QSI share)", [
            ("Origin capture share", f"{float(dem.get('qsi_share') or 0) * 100:.1f}%", "calibrated",
             "this route's schedule quality vs every existing itinerary (industry QSI form); "
             "coefficients calibrated on launched-route outturn - see Track record"),
        ]),
        ("C &middot; Coverage", [
            ("GDS coverage gross-up", f"x{float(dem.get('coverage_gross_up') or 1):.2f}", "calibrated",
             "measured against airports' own passenger counts; corrects for off-GDS sales"),
        ]),
        ("D &middot; Stimulation", [
            ("New-service stimulation", f"x{float(dem.get('stimulation') or 1):.2f}", "calibrated",
             "by carrier type, from launched-route outcomes; induced markets graded separately"),
        ]),
        ("E &middot; Connecting feed", [
            ("Behind the origin, each way/yr", f(dem.get("feed_behind")), "calibrated",
             "each feeder itinerary scored for connection quality (legal time, elapsed, alliance); "
             "share of the measured connecting market"),
            ("Beyond the destination, each way/yr", f(dem.get("feed_beyond")), "calibrated",
             "same method over the destination hub's onward wave; departure time moves this"),
        ]),
        ("F &middot; Aircraft and economics", [
            ("Equipment / frequency", f"{esc(str(cap.get('aircraft', '?')))} &middot; "
             f"{cap.get('freq', '?')}x/wk", "user",
             "user choice or profit-ranked within the airline's real fleet"),
            ("Achieved load factor", f"{float(cap.get('load') or 0) * 100:.0f}%", "physics",
             "demand filled against seats x frequency"),
            ("Maintenance basis", esc(str(raw.get("maint_basis", "-"))), "calibrated",
             "sector-aware reserves validated against OEM data"),
            ("Ownership basis", esc(str(raw.get("own_basis", "-"))), "calibrated",
             "appraiser value/lease anchors, blended by airline type and age"),
        ]),
        ("G &middot; Constraints", [
            ("Capacity cap, each way/yr", f(cap.get("carried")), "physics",
             "the forecast never exceeds what the metal carries"),
            ("Airfield check", esc(str(af.get("band", "not assessed"))), "physics",
             esc(str(af.get("note", "runway/elevation capability vs the chosen type")))[:120]),
        ]),
    ]
    cards = "".join(
        f'<div class="xstage"><div class="xh">{name}</div>'
        f'<table class="xtab"><tr><th>assumption</th><th>this run</th><th>source</th>'
        f'<th>basis</th></tr>{rows(items)}</table></div>'
        for name, items in stages)
    return f"""
  <div class="card">
    <details>
      <summary><b>Expert detail: the engine room</b> <span class="sub">every assumption in this
      forecast, tagged by provenance - for network planners who want to challenge the number</span></summary>
      <div class="legend" style="margin:10px 0 4px">
        <span><span class="tag measured">measured</span> read from data, not assumed</span>
        <span><span class="tag calibrated">calibrated</span> fitted to launched-route outcomes</span>
        <span><span class="tag physics">physics</span> capacity and airfield limits</span>
        <span><span class="tag user">user</span> analyst choice, overridable in Expert mode</span>
      </div>
      {cards}
      <div class="note" style="margin-top:10px">Route-specific values are shown in full - they
      appear in any client report. The calibrated global constants and functional forms behind
      the "calibrated" tags are Avia's engine and are described by provenance and validation
      (the Track record page), not by value. Every "user" row can be overridden in Expert mode
      and the log will show the override.</div>
    </details>
  </div>"""


def render(last=None):
    esc = _html.escape
    have = bool(last and isinstance(last, dict) and last.get("fc"))
    if have:
        fc = last["fc"]
        o, d = fc.get("origin", {}), fc.get("dest", {})
        title = f'{o.get("city", o.get("iata", "?"))} to {d.get("city", d.get("iata", "?"))}'
        who = fc.get("airline") or "new entrant"
        cap = fc.get("capacity") or {}
        sub = (f'{who} &middot; {cap.get("aircraft", "?")} &middot; '
               f'{cap.get("freq", "?")}x weekly - the forecast last run on the dashboard')
        bridge = _bridge_svg(_bridge_from_fc(fc))
        bridge_head = f"Your number, assembled: {esc(title)}"
    else:
        sub = ""
        bridge = (f'<div class="note" style="padding:26px;text-align:center">Run a forecast on '
                  f'the <a href="/">dashboard</a> and revisit this page: the chart here will '
                  f'rebuild YOUR number step by step, with the weight of every element.</div>')
        bridge_head = "Your number, assembled"

    steps_html = "".join(
        f'<div class="step"><div class="n">{n}</div><div><div class="st">{esc(t)}</div>'
        f'<div class="sd">{esc(dsc)}</div></div></div>'
        for n, t, dsc in STEPS)

    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Methodology &middot; The Observatory · Meridian</title>
{FONT_LINK}
<style>
  *{{box-sizing:border-box}}
  body{{font-family:{SERIF};background:{SCREEN};color:{INKTX};margin:0;font-size:14.5px;line-height:1.6}}
  .wrap{{max-width:1120px;margin:0 auto;padding:30px 28px 64px}}
  h1{{font-family:{SERIF};font-weight:300;color:{INK};font-size:28px;margin:8px 0 4px}}
  h2{{font-family:{SERIF};font-weight:500;color:{INK};font-size:18px;margin:0 0 10px}}
  .sub{{font-family:{SERIF};color:{BODY};font-size:14px;line-height:1.55}}
  .note{{font-family:{SERIF};color:{BODY};font-size:13px;line-height:1.6}}
  .topnav{{display:flex;gap:18px;margin-bottom:14px;font-family:{SANS};font-size:10px;letter-spacing:.1em;text-transform:uppercase;font-weight:600}}
  .topnav a{{color:{INK};text-decoration:none;border-bottom:1px solid {BRASS};padding-bottom:2px}}
  .kicker{{font-family:{SANS};font-size:9px;letter-spacing:.2em;text-transform:uppercase;color:{MUT};font-weight:600}}
  .card{{background:{PAPER};border:1px solid {LINE};border-radius:2px;padding:22px;margin-top:16px}}
  .step{{display:flex;gap:16px;padding:12px 0;border-bottom:1px solid {LINE}}}
  .step:last-child{{border-bottom:none}}
  .n{{flex:0 0 30px;height:30px;background:{INK};color:{PAPER};display:flex;
      align-items:center;justify-content:center;font-family:{SANS};font-weight:600;font-size:12px}}
  .st{{font-family:{SERIF};font-weight:600;color:{INK};font-size:15px}} .sd{{font-family:{SERIF};color:{BODY};font-size:13.5px;line-height:1.6;margin-top:3px}}
  .legend{{display:flex;gap:18px;font-family:{SANS};font-size:10px;letter-spacing:.05em;text-transform:uppercase;color:{MUT};margin-top:10px;flex-wrap:wrap}}
  .sw{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px}}
  details summary{{cursor:pointer;font-family:{SERIF};font-size:15px;color:{INK}}}
  .xstage{{margin-top:16px}} .xh{{font-family:{SANS};font-weight:600;color:{MUT};font-size:10px;letter-spacing:.12em;text-transform:uppercase;margin-bottom:6px}}
  .xtab{{border-collapse:collapse;width:100%;font-family:{SERIF};font-size:12.5px}}
  .xtab th{{text-align:left;font-family:{SANS};font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:{MUT};font-weight:600;padding:6px 8px;border-bottom:1px solid {INK}}}
  .xtab td{{padding:6px 8px;border-bottom:1px solid {LINE};vertical-align:top;color:{BODY}}}
  .xtab td.v{{font-weight:500;color:{INK};white-space:nowrap;font-variant-numeric:tabular-nums lining-nums}} .xtab td.nt{{color:{MUT}}}
  .tag{{display:inline-block;border:1px solid {LINE};border-radius:2px;padding:1px 8px;font-family:{SANS};font-size:9px;letter-spacing:.06em;text-transform:uppercase;font-weight:600}}
  .tag.measured{{color:#3D6A88;border-color:#3D6A88}} .tag.calibrated{{color:#5F8D7A;border-color:#5F8D7A}}
  .tag.physics{{color:#A9553F;border-color:#A9553F}} .tag.user{{color:#7B617F;border-color:#7B617F}}
  :focus-visible{{outline:2px solid {BRASS};outline-offset:2px}}
</style></head><body><div class="wrap">
  <div class="topnav"><a href="/">&larr; Route Forecasting</a>
    <a href="/trackrecord">Track Record</a></div>
  <div class="kicker">The Observatory &middot; Meridian &middot; How a forecast is built</div>
  <h1>Methodology</h1>
  <div class="sub">Every number in a Meridian forecast is either measured, calibrated against
  launched-route outcomes, or capped by physics - and each step below is visible in the output,
  so a client can challenge any of them. How well this process performs is published per airport
  on the <a href="/trackrecord">Track record</a> page.</div>

  <div class="card">
    <h2>{bridge_head}</h2>
    <div class="sub">{sub}</div>
    {bridge}
    <div class="legend">
      <span><span class="sw" style="background:{NAVY}"></span>measured starting point</span>
      <span><span class="sw" style="background:{RED}"></span>reduces the number</span>
      <span><span class="sw" style="background:{GREEN}"></span>adds to the number</span>
      <span><span class="sw" style="background:{ACCENT}"></span>the forecast</span>
    </div>
  </div>

  <div class="card">
    <h2>The six steps</h2>
    {steps_html}
  </div>

  {_expert_section(last["fc"]) if have else ""}

  <div class="note" style="margin-top:14px">
    Passengers are annual, each way. The capture and feed shares use the industry QSI method -
    the same scoring airlines' own network planners use - calibrated so that, across every new
    route launched in the graded sample, the median forecast matches what routes actually
    carried. Indicative, for directional guidance; the full assumptions register accompanies
    every report.
  </div>
</div></body></html>"""


if __name__ == "__main__":
    # offline preview with an illustrative example (Genoa-New York shaped numbers)
    example = {"fc": {
        "ok": True,
        "origin": {"city": "Genoa", "iata": "GOA"}, "dest": {"city": "New York", "iata": "JFK"},
        "airline": "example airline",
        "demand": {"natural": 155000, "qsi_share": 0.42, "coverage_gross_up": 1.18,
                   "stimulation": 1.15, "captured": 88300, "feed_behind": 6200,
                   "feed_beyond": 9800, "total": 104300},
        "capacity": {"carried": 96400, "aircraft": "A321XLR", "freq": 7},
    }}
    print(render(example))
