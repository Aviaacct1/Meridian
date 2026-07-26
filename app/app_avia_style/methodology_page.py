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

NAVY, ACCENT, MUT, BG = "#0b2545", "#1f6feb", "#5b6b7c", "#f5f7fa"
GREEN, RED = "#1a7f4b", "#b3423a"

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
    out = [f'<svg viewBox="0 0 {W} {H}" style="width:100%;max-width:{W}px" '
           f'font-family="Segoe UI,system-ui,sans-serif">']
    out.append(f'<line x1="{padl}" y1="{y(0)}" x2="{W-padr}" y2="{y(0)}" stroke="#d7dee7"/>')
    prev_end = None
    for i, ((label, sub, v, kind), (lo, hi)) in enumerate(zip(bars, levels)):
        x = padl + i * bw + 6
        w = bw - 12
        col = {"start": NAVY, "total": ACCENT, "up": GREEN, "down": RED}[kind]
        out.append(f'<rect x="{x:.0f}" y="{y(hi):.0f}" width="{w:.0f}" '
                   f'height="{max(2, (hi-lo)*sy):.0f}" rx="4" fill="{col}" opacity="0.9"/>')
        if prev_end is not None:                          # connector
            out.append(f'<line x1="{x-6:.0f}" y1="{y(prev_end):.0f}" x2="{x:.0f}" '
                       f'y2="{y(prev_end):.0f}" stroke="{MUT}" stroke-dasharray="3 3" opacity="0.6"/>')
        prev_end = hi if kind in ("start", "up", "total") else lo
        val = hi if kind in ("start", "total") else abs(v)
        sign = "" if kind in ("start", "total") else ("+" if kind == "up" else "−")
        out.append(f'<text x="{x+w/2:.0f}" y="{y(hi)-6:.0f}" text-anchor="middle" font-size="12" '
                   f'font-weight="700" fill="{NAVY}">{sign}{_fmt(val)}</text>')
        out.append(f'<text x="{x+w/2:.0f}" y="{H-padb+18}" text-anchor="middle" font-size="11.5" '
                   f'font-weight="600" fill="{NAVY}">{label}</text>')
        out.append(f'<text x="{x+w/2:.0f}" y="{H-padb+33}" text-anchor="middle" font-size="10" '
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
<title>Methodology - Avia Cortex</title>
<style>
  body{{font-family:Segoe UI,system-ui,-apple-system,sans-serif;background:{BG};color:#17222e;margin:0}}
  .wrap{{max-width:1000px;margin:0 auto;padding:26px 18px 60px}}
  h1{{color:{NAVY};font-size:24px;margin:6px 0 2px}} h2{{color:{NAVY};font-size:16px;margin:0 0 10px}}
  .sub{{color:{MUT};font-size:13px}} .note{{color:{MUT};font-size:12.5px;line-height:1.5}}
  .topnav{{display:flex;gap:14px;margin-bottom:10px;font-size:12.5px}}
  .topnav a{{color:{ACCENT};text-decoration:none;font-weight:600}}
  .card{{background:#fff;border:1px solid #e3e9f0;border-radius:12px;padding:20px;margin-top:14px}}
  .step{{display:flex;gap:14px;padding:11px 0;border-bottom:1px solid #eef2f6}}
  .step:last-child{{border-bottom:none}}
  .n{{flex:0 0 30px;height:30px;border-radius:50%;background:{NAVY};color:#fff;display:flex;
      align-items:center;justify-content:center;font-weight:700;font-size:13px}}
  .st{{font-weight:700;color:{NAVY};font-size:13.5px}} .sd{{color:#3d4a58;font-size:12.5px;line-height:1.55;margin-top:2px}}
  .legend{{display:flex;gap:16px;font-size:11px;color:{MUT};margin-top:6px;flex-wrap:wrap}}
  .sw{{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:-1px}}
  details summary{{cursor:pointer;font-size:14px;color:{NAVY}}}
  .xstage{{margin-top:14px}} .xh{{font-weight:700;color:{NAVY};font-size:12.5px;margin-bottom:4px}}
  .xtab{{border-collapse:collapse;width:100%;font-size:12px}}
  .xtab th{{text-align:left;color:{MUT};font-weight:600;padding:4px 8px;border-bottom:1.5px solid #e3e9f0}}
  .xtab td{{padding:4px 8px;border-bottom:1px solid #eef2f6;vertical-align:top}}
  .xtab td.v{{font-weight:700;color:{NAVY};white-space:nowrap}} .xtab td.nt{{color:{MUT}}}
  .tag{{display:inline-block;border-radius:99px;padding:1px 8px;font-size:10px;font-weight:700}}
  .tag.measured{{background:#e8f1fd;color:{ACCENT}}} .tag.calibrated{{background:#eaf6ef;color:{GREEN}}}
  .tag.physics{{background:#f4ecec;color:{RED}}} .tag.user{{background:#f0eefa;color:#6d5bd0}}
</style></head><body><div class="wrap">
  <div class="topnav"><a href="/">&larr; Route Forecasting</a>
    <a href="/trackrecord">Track record</a></div>
  <div class="sub">Avia Cortex &middot; how a forecast is built</div>
  <h1>Methodology</h1>
  <div class="sub">Every number in a Cortex forecast is either measured, calibrated against
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
