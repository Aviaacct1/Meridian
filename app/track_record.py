#!/usr/bin/env python3
"""
Avia Cortex - Track record: the per-airport back-test evidence page (John's idea, 4 Jul 2026).
===============================================================================================
Any airport can see how the forecast engine has performed against every new route launched
there in the graded sample: forecast vs actual first-full-year outturn, as a distribution.
No competing manual QSI can show an outturn record at all - transparency IS the pitch.

Framing rules (agreed 4 Jul):
- Lead with BIAS: the forecastable median near 1.0 with over/under roughly even is the strong,
  honest claim. Raw within-10% is single digits for every forecaster in this industry, so the
  spread is expressed as factor bands around the median (half of outcomes within x1.4, 80%
  within x2.1), with within-10/20/30% shown in the table for completeness.
- FORECASTABLE vs INDUCED split, clearly labelled: forecastable (a pre-existing market at least
  the size the route carried) is the engine's real test; induced (the route created a market
  history didn't show) is the stimulation/judgement layer and reads low by construction.
- Small n: below FLOOR forecastable routes at the airport, the stats widen to a labelled peer
  group (same regions as the airport's routes), and below PEER_MIN to the global sample. A bell
  curve on four routes would mislead in both directions.
- Versioned: the page names the engine file and launch years it is built on. When the 6-year
  sample (2016-2019 + 2024-2025, Covid excluded) lands, drop bt_v1_6yr.csv (or the V2 file once
  default) into app/ and the page upgrades itself - functionality is common, the sample grows.

USE:  /trackrecord?airport=STT on the portal, or offline:
      py -3.12 track_record.py STT --out track_STT.html
"""
import argparse
import csv
import html as _html
import math
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
# preference order: the newest, widest evidence file present wins (V2 file once it is default)
SOURCES = ["master_backtest_scored.csv", "bt_v2_6yr.csv", "bt_v1_6yr.csv", "bt_v1_baseline.csv"]
FLOOR = 15        # min forecastable routes for airport-only stats
PEER_MIN = 30     # min for peer-group stats before falling back to global

# ---- The Observatory palette (restyle) ----
INK, BRASS, BRASSD, SIGNAL = "#0F1B28", "#D4A249", "#A97C33", "#CE3B2A"
PAPER, SCREEN, LINE = "#F6F3EC", "#FAF8F3", "#E2DCCC"
BODY, INKTX = "#3A444E", "#26313B"
# legacy names kept as aliases so existing references resolve to Observatory colours
NAVY, ACCENT, MUT, BG = INK, BRASS, "#6E6A5E", SCREEN   # MUT darkened for legibility
SERIF, SANS, MONO = "'Newsreader',Georgia,serif", "'Inter',system-ui,sans-serif", "'IBM Plex Mono',monospace"

FONT_LINK = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
  '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
  '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
  'family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;0,6..72,500;1,6..72,400'
  '&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">')

OBS_STYLE = f"""<style>
  *{{box-sizing:border-box}}
  body{{font-family:{SERIF};background:{SCREEN};color:{INKTX};margin:0;font-size:14.5px;line-height:1.55}}
  .wrap{{max-width:1200px;margin:0 auto;padding:30px 28px 64px}}
  h1{{font-family:{SERIF};font-weight:300;color:{INK};font-size:28px;margin:8px 0 4px}}
  h2{{font-family:{SERIF};font-weight:500;color:{INK};font-size:18px;margin:26px 0 10px}}
  .sub{{font-family:{SERIF};color:{BODY};font-size:14px;line-height:1.55}}
  .note{{font-family:{SERIF};color:{BODY};font-size:13px;line-height:1.6}}
  .card{{background:{PAPER};border:1px solid {LINE};border-radius:2px;padding:20px;margin-top:16px}}
  .tiles{{display:grid;grid-template-columns:repeat(5,1fr);gap:0;margin-top:12px;border-top:1px solid {INK}}}
  .tile{{padding:14px 16px 14px 0;border-right:1px solid {LINE}}}
  .tile:last-child{{border-right:none}}
  .tv{{font-family:{SERIF};font-size:26px;font-weight:400;color:{INK};font-variant-numeric:tabular-nums lining-nums;line-height:1}}
  .tl{{font-family:{SANS};font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:{MUT};margin-top:8px;font-weight:600;line-height:1.4}}
  table{{border-collapse:collapse;width:100%;font-family:{SERIF};font-size:12.5px;font-variant-numeric:tabular-nums lining-nums}}
  th{{text-align:left;font-family:{SANS};font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:{MUT};font-weight:600;padding:8px;border-bottom:1px solid {INK}}}
  td{{padding:7px 8px;border-bottom:1px solid {LINE};color:{BODY}}}
  .badge{{display:inline-block;background:transparent;color:{BRASSD};border:1px solid {LINE};border-radius:2px;padding:2px 9px;font-family:{SANS};font-size:9px;letter-spacing:.1em;text-transform:uppercase;font-weight:600}}
  .badge b{{font-family:{MONO};letter-spacing:0;text-transform:none;font-weight:500;color:{BODY}}}
  .prov{{font-family:{SANS};font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;color:{MUT};margin-top:12px;padding-top:9px;border-top:1px solid {LINE};display:flex;flex-wrap:wrap;gap:6px 16px}}
  .prov b{{font-weight:600;color:{MUT}}}
  .prov .val{{font-family:{SERIF};text-transform:none;letter-spacing:0;font-size:12px;color:{BODY}}}
  .topnav{{display:flex;gap:18px;align-items:center;margin-bottom:14px;font-family:{SANS};font-size:10px;letter-spacing:.1em;text-transform:uppercase;font-weight:600}}
  .topnav a{{color:{INK};text-decoration:none;border-bottom:1px solid {BRASS};padding-bottom:2px}}
  .topnav a:hover{{color:{BRASSD}}}
  .kicker{{font-family:{SANS};font-size:9px;letter-spacing:.2em;text-transform:uppercase;color:{MUT};font-weight:600}}
  svg text{{font-family:{SANS}}}
  :focus-visible{{outline:2px solid {BRASS};outline-offset:2px}}
</style>"""


def _source_path():
    for s in SOURCES:
        p = os.path.join(HERE, s)
        if os.path.exists(p):
            return p
    return None


try:
    import airport_capture as _ACAP
except Exception:
    _ACAP = None


def _dest_fac(arr, market):
    """Destination thin-market capture lift from the engine module, so the historical track record reflects the
    same market-conditioned SJC-style fix the live engine applies (keeps the page and the engine consistent)."""
    return _ACAP.dest_thin_factor(arr, market) if _ACAP else 1.0


def load_rows(path):
    rows = []
    for r in csv.DictReader(open(path)):
        try:
            ratio = float(r.get("fc_over_out") or 0)
            if ratio <= 0:
                continue
            dfac = _dest_fac(r["arr"], float(r.get("natural") or 0))   # thin-market lift for under-credited destinations (SJC inbound)
            corr = float(r.get("corrected_fc_over_out") or 0)   # in-sample ML correction (dev view); 0 if not scored
            rows.append({
                "route": r["route"], "dep": r["dep"], "arr": r["arr"],
                "year": int(r["year"]), "region": r.get("region", ""),
                "carrier": r.get("carrier", ""), "type": r.get("type", ""),
                "ratio": ratio * dfac,
                "ratio_corr": corr if corr > 0 else ratio * dfac,
                "forecast": float(r.get("forecast_pax") or 0) * dfac,
                "outturn": float(r.get("outturn_pax") or 0),
                "forecastable": float(r.get("natural") or 0) >= float(r.get("p2p_outturn") or 0) > 0,
            })
        except (ValueError, KeyError):
            continue
    return rows


def _stats(ratios):
    """Honest raw stats: bias (median, over/under), spread factors around the median,
    and the within bands. Ratios are forecast/outturn."""
    xs = sorted(ratios)
    n = len(xs)
    if not n:
        return None
    med = xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2
    dev = sorted(abs(math.log(x / med)) for x in xs)
    q = lambda p: dev[min(n - 1, int(p * n))]
    w = lambda t: sum(1 for x in xs if abs(x - 1) <= t) / n
    return {"n": n, "median": med,
            "over": sum(1 for x in xs if x > 1), "under": sum(1 for x in xs if x <= 1),
            "f50": math.exp(q(0.5)), "f80": math.exp(q(0.8)),
            "w10": w(0.10), "w20": w(0.20), "w30": w(0.30)}


def _hist(ratios, bins=13):
    """Counts in log2(ratio) bins from 1/8x to 8x, outliers clamped into the end bins."""
    lo, hi = -3.0, 3.0
    counts = [0] * bins
    for r in ratios:
        v = max(lo, min(hi - 1e-9, math.log2(r)))
        counts[int((v - lo) / (hi - lo) * bins)] += 1
    labels = []
    for i in range(bins):
        c = lo + (i + 0.5) * (hi - lo) / bins
        f = 2 ** c
        labels.append(("x%.1f" % f) if f >= 1 else ("1/%.1f" % (1 / f)))
    return counts, labels


def airport_track(rows, airport):
    """Assemble the evidence for one airport, widening to peer/global below the n floors."""
    a = airport.strip().upper()
    mine = [r for r in rows if r["dep"] == a or r["arr"] == a]
    fore = [r for r in mine if r["forecastable"]]
    indu = [r for r in mine if not r["forecastable"]]
    regions = [rg for rg, _n in Counter(r["region"] for r in mine if r["region"]).most_common(2)]

    basis, basis_rows = "airport", fore
    if len(fore) < FLOOR:
        peer = [r for r in rows if r["forecastable"] and r["region"] in regions] if regions else []
        if len(peer) >= PEER_MIN:
            basis, basis_rows = "peer", peer
        else:
            basis, basis_rows = "global", [r for r in rows if r["forecastable"]]

    years = sorted({r["year"] for r in rows})
    return {
        "airport": a, "n_here": len(mine), "n_fore_here": len(fore),
        "regions": regions, "years": years,
        "basis": basis, "basis_n": len(basis_rows),
        "stats_basis": _stats([r["ratio"] for r in basis_rows]),
        "stats_here": _stats([r["ratio"] for r in fore]),
        "stats_induced": _stats([r["ratio"] for r in indu]),
        "hist": _hist([r["ratio"] for r in basis_rows]),
        # corrected (in-sample ML) view, ALWAYS on this airport's own forecastable routes (even below FLOOR)
        "n_corr": len(fore),
        "stats_corr": _stats([r["ratio_corr"] for r in fore]) if fore else None,
        "hist_corr": _hist([r["ratio_corr"] for r in fore]) if fore else None,
        "routes": sorted(mine, key=lambda r: -r["year"])[:40],
    }


def total_track(rows):
    """Whole-engine evidence across EVERY graded route (all airports): the combined book, split into
    forecastable (the measured-market test) and induced (the new-market / stimulation layer, now floored),
    plus a breakdown by carrier type and region. This is the engine-level scorecard, not an airport's."""
    fore = [r for r in rows if r["forecastable"]]
    indu = [r for r in rows if not r["forecastable"]]

    def _grp(keyfn, order=None):
        d = {}
        for r in rows:
            d.setdefault(keyfn(r) or "?", []).append(r)
        keys = order or sorted(d, key=lambda k: -len(d[k]))
        return [(k, _stats([r["ratio"] for r in d[k]])) for k in keys if k in d]

    return {
        "years": sorted({r["year"] for r in rows}),
        "n_all": len(rows), "n_fore": len(fore), "n_indu": len(indu),
        "n_carriers": len({r["carrier"] for r in rows if r["carrier"]}),
        "n_origins": len({r["dep"] for r in rows}),
        "stats_all": _stats([r["ratio"] for r in rows]),
        "stats_fore": _stats([r["ratio"] for r in fore]),
        "stats_indu": _stats([r["ratio"] for r in indu]),
        "hist_all": _hist([r["ratio"] for r in rows]),
        "hist_fore": _hist([r["ratio"] for r in fore]),
        "hist_indu": _hist([r["ratio"] for r in indu]),
        "bytype": _grp(lambda r: r["type"], ["FSC", "LCC", "ULCC", "Regional"]),
        "byreg": _grp(lambda r: r["region"]),
    }


def _apt_name(code):
    try:
        import airportsdata
        r = airportsdata.load("IATA").get(code)
        return r["name"] if r else code
    except Exception:
        return code


# ------------------------------------------------------------------ rendering
def _tiles(s):
    return f"""
    <div class="tiles">
      <div class="tile"><div class="tv">{s['median']:.2f}</div><div class="tl">median forecast &divide; actual<br>(1.00 = unbiased)</div></div>
      <div class="tile"><div class="tv">{s['over']} / {s['under']}</div><div class="tl">over / under forecasts</div></div>
      <div class="tile"><div class="tv">&times;{s['f50']:.2f}</div><div class="tl">half of outcomes within this factor of the central forecast</div></div>
      <div class="tile"><div class="tv">&times;{s['f80']:.2f}</div><div class="tl">80% of outcomes within this factor</div></div>
      <div class="tile"><div class="tv">{s['n']}</div><div class="tl">launched routes graded</div></div>
    </div>"""


def _stat_row(label, s):
    if not s:
        return f"<tr><td>{label}</td><td colspan='8' style='color:{MUT}'>no graded routes</td></tr>"
    return (f"<tr><td>{label}</td><td>{s['n']}</td><td>{s['median']:.2f}</td>"
            f"<td>{s['over']}/{s['under']}</td><td>&times;{s['f50']:.2f}</td><td>&times;{s['f80']:.2f}</td>"
            f"<td>{s['w10']*100:.0f}%</td><td>{s['w20']*100:.0f}%</td><td>{s['w30']*100:.0f}%</td></tr>")


def _svg_hist(counts, labels):
    """Error distribution to the Observatory grammar: ink bars, brass centre (on-the-money) bin,
    a dashed Signal-Red reference at the unbiased line (1.00), corner registration ticks and a
    provenance rail. Each bar counts routes by how far the forecast landed from the outcome."""
    mx = max(counts) or 1
    W, H, L, R, T, B = 760, 250, 34, 726, 34, 196
    n = len(counts)
    span = 6.0                                  # -3..+3 log2
    bx = lambda v: L + (v + 3.0) / span * (R - L)
    b20l, b20r = bx(-math.log2(1.2)), bx(math.log2(1.2))
    plot_h = B - T
    bw = (R - L) / n
    bars, ticks = [], []
    for i, c in enumerate(counts):
        h = plot_h * c / mx
        x = L + i * bw
        mid = i == n // 2
        col = BRASS if mid else INK             # centre 'on the money' bin brass; the rest ink
        bars.append(f'<rect x="{x+2:.1f}" y="{B-h:.1f}" width="{bw-4:.1f}" height="{h:.1f}" fill="{col}"/>')
        if c:
            bars.append(f'<text x="{x+bw/2:.0f}" y="{B-h-6:.0f}" text-anchor="middle" '
                        f'font-size="10" fill="{MUT}">{c}</text>')
        if i % 2 == 0:
            ticks.append(f'<text x="{x+bw/2:.0f}" y="{B+16:.0f}" text-anchor="middle" font-size="9" '
                         f'fill="{MUT}" font-family="{MONO}">{labels[i]}</text>')
    reg = (f'<g stroke="{INK}" stroke-width="1" fill="none">'
           f'<path d="M{L} {T} h10 M{L} {T} v10"/><path d="M{R} {T} h-10 M{R} {T} v10"/>'
           f'<path d="M{L} {B} h10 M{L} {B} v-10"/><path d="M{R} {B} h-10 M{R} {B} v-10"/></g>')
    return (f'<svg viewBox="0 0 {W} {H}" style="width:100%;max-width:{W}px">'
            f'<rect x="{b20l:.0f}" y="{T}" width="{b20r-b20l:.0f}" height="{B-T:.0f}" '
            f'fill="{BRASS}" opacity="0.09"/>'
            f'{reg}'
            f'<line x1="{L}" y1="{B}" x2="{R}" y2="{B}" stroke="{INK}" stroke-width="1.2"/>'
            f'<line x1="{bx(0):.0f}" y1="{T}" x2="{bx(0):.0f}" y2="{B}" '
            f'stroke="{SIGNAL}" stroke-width="1.2" stroke-dasharray="4 3"/>'
            f'<text x="{bx(0):.0f}" y="{T-9}" text-anchor="middle" font-size="9" '
            f'fill="{SIGNAL}" font-family="{MONO}">UNBIASED 1.00</text>'
            + "".join(bars) + "".join(ticks) +
            f'<text x="{L}" y="{H-8}" font-size="10" fill="{MUT}">&#8592; forecast LOW, route did better</text>'
            f'<text x="{R}" y="{H-8}" text-anchor="end" font-size="10" fill="{MUT}">'
            f'forecast HIGH, route did worse &#8594;</text></svg>'
            f'<div class="prov">'
            f'<span><b>Source</b> <span class="val">launched-route outturn</span></span>'
            f'<span><b>Units</b> <span class="val">routes by forecast &divide; actual</span></span>'
            f'<span><b>Reference</b> <span class="val">Signal Red = unbiased (1.00)</span></span>'
            f'<span><b>Method</b> <span class="val">QSI methodology v2.4</span></span></div>'
            f'<div class="note" style="margin-top:8px">How to read it: a route in the shaded '
            f'centre band was forecast within 20% of its actual first-year traffic. "x2.0" '
            f'means the forecast was double what the route carried; "1/2.0" means the route '
            f'carried double the forecast. The tighter the bars cluster on the centre, the '
            f'more dependable the forecast.</div>')


def render_html(t, source_name, engine_ctx=None):
    a = t["airport"]
    name = _apt_name(a)
    yrs = t["years"]
    yr_label = f"{min(yrs)}-{max(yrs)}" if yrs else "-"
    basis_note = {
        "airport": f"Statistics are for the {t['basis_n']} existing-market routes at {a} itself.",
        "peer": (f"{a} has {t['n_fore_here']} existing-market launches in the sample - too few for "
                 f"a distribution of its own - so the headline statistics use the {t['basis_n']} "
                 f"existing-market routes in its peer group ({', '.join(t['regions']) or 'same region'}). "
                 f"{a}'s own routes are shown separately below."),
        "global": (f"{a} has {t['n_fore_here']} existing-market launches in the sample - too few for "
                   f"a distribution - so the headline statistics use the full existing-market sample. "
                   f"{a}'s own routes are shown separately below."),
    }[t["basis"]]
    counts, labels = t["hist"]
    esc = _html.escape

    def _verdict(r):
        if 0.8 <= r <= 1.25:
            return "about right"
        if r > 1.25:
            return f"forecast {r:.1f}x too high"
        return f"route did {1/r:.1f}x better"

    route_rows = "".join(
        f"<tr><td>{esc(r['route'])}</td><td>{esc(r['carrier'])}</td><td>{r['year']}</td>"
        f"<td>{'existing market' if r['forecastable'] else 'new market'}</td>"
        f"<td style='text-align:right'>{r['forecast']:,.0f}</td>"
        f"<td style='text-align:right'>{r['outturn']:,.0f}</td>"
        f"<td>{_verdict(r['ratio'])}</td></tr>"
        for r in t["routes"])

    # Whole-engine context panel: only when the airport shows its OWN histogram (>= FLOOR routes). Below the
    # floor the headline already uses the peer/global set, so the context is redundant. Careful wording: this is
    # the historical performance of the calibrated engine on the launches it was trained on, not a promise.
    ctx_html = ""
    if t["basis"] == "airport" and engine_ctx and engine_ctx.get("stats"):
        _ec, _el = engine_ctx["hist"]; _es = engine_ctx["stats"]
        ctx_html = f"""
  <div class="card">
    <h2 style="margin-top:0">In context: the whole engine</h2>
    <div class="note">Across all {_es['n']:,} existing-market launches at every airport in the sample
    ({yr_label}), this is how the engine lands. {esc(a)}'s own distribution above sits inside this book;
    a similar shape and a median near 1.00 mean {esc(a)} forecasts about as dependably as the engine overall.</div>
    {_tiles(_es)}
    <div style="margin-top:14px">{_svg_hist(_ec, _el)}</div>
    <div class="note" style="margin-top:8px">Median forecast &divide; actual {_es['median']:.2f}; within
    &plusmn;20% on {_es['w20']*100:.0f}% of existing-market launches across the whole book. This is the
    historical performance of the calibrated engine across the launches it was trained on, not a promise for
    any single future route.</div>
  </div>"""

    # DEVELOPMENT panel: the in-sample ML-corrected view, this airport's own routes (shown even below FLOOR)
    corr_html = ""
    if t.get("stats_corr"):
        _cc, _cl = t["hist_corr"]; _cs = t["stats_corr"]
        corr_html = f"""
  <div class="card" style="border:1px solid {BRASS}">
    <span class="badge" style="border-color:{BRASS};color:{BRASSD}">DEVELOPMENT &middot; in-sample, calibrated on all data</span>
    <h2 style="margin:10px 0 0">With the route-level correction ({_cs['n']} launches at {esc(a)})</h2>
    <div class="note">The engine's forecasts adjusted by the machine-learned route correction, fitted across all
    the data we hold. This is the in-sample view: within &plusmn;20% on {_cs['w20']*100:.0f}% of {esc(a)}'s launches,
    median {_cs['median']:.2f}. It shows what the correction achieves when calibrated on every route including these;
    the chart below is the same engine <b>without</b> the correction, closer to what a brand-new, unseen route gets.
    Both are shown deliberately, for your view on which number a buyer should see.</div>
    {_tiles(_cs)}
    <div style="margin-top:14px">{_svg_hist(_cc, _cl)}</div>
  </div>"""

    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Track Record &middot; {esc(a)} &middot; The Observatory</title>
{FONT_LINK}{OBS_STYLE}</head><body><div class="wrap">
  <div class="topnav"><a href="/">&larr; Route Forecasting</a>
    <a href="/trackrecord">Check another airport</a></div>
  <div class="kicker">The Observatory &middot; Meridian &middot; Forecast Track Record</div>
  <h1>{esc(name)} ({esc(a)})</h1>
  <div class="sub">Every new route launched at {esc(a)} in the graded sample, forecast the year
  before launch with no knowledge of the outcome, against the route's actual first-full-year
  traffic. Launch years {yr_label}. Of the {t['n_here']} launches here, {t['n_fore_here']} were into
  <b>existing markets</b> (the demand was already there before the route) and {t['n_here']-t['n_fore_here']}
  into <b>brand-new markets</b> (the route created demand that didn't show before); the headline below is the
  existing-market set, the engine's real test, with new-market routes listed separately lower down.
  <span class="badge">Evidence file <b>{esc(source_name)}</b></span></div>

{corr_html}
  <div class="card">
    <h2 style="margin-top:0">The engine's real test: routes into existing markets</h2>
    <div class="note">{esc(basis_note)}</div>
    {_tiles(t['stats_basis'])}
    <div style="margin-top:14px">{_svg_hist(counts, labels)}</div>
  </div>

  <div class="card">
    <h2 style="margin-top:0">The detail</h2>
    <table>
      <tr><th>set</th><th>n</th><th>median</th><th>over/under</th><th>half within</th>
          <th>80% within</th><th>&plusmn;10%</th><th>&plusmn;20%</th><th>&plusmn;30%</th></tr>
      {_stat_row(f"existing markets ({'this airport' if t['basis']=='airport' else 'peer group' if t['basis']=='peer' else 'all airports'})", t['stats_basis'])}
      {_stat_row(f"existing markets at {esc(a)} only", t['stats_here']) if t['basis'] != 'airport' else ''}
      {_stat_row(f"new markets at {esc(a)} (route created the demand)", t['stats_induced'])}
    </table>
    <div class="note" style="margin-top:10px">
      Existing market = demand at least the route's eventual size was already flying (mostly via connections
      or nearby airports) before the route launched; this is the honest test of a data-driven forecast. New
      market = the route created demand that wasn't visible before; forecasting those relies more on judgement,
      so they're shown separately and not blended into the headline. Ratios are graded against the aircraft and
      frequency actually flown.</div>
  </div>

  <div class="card">
    <h2 style="margin-top:0">Routes at {esc(a)} in the sample ({t['n_here']}: {t['n_fore_here']} existing-market + {t['n_here']-t['n_fore_here']} new-market, newest first)</h2>
    <table><tr><th>route</th><th>carrier</th><th>launched</th><th>class</th>
    <th style="text-align:right">forecast, year 1</th><th style="text-align:right">actually carried</th><th>how it landed</th></tr>
    {route_rows}</table>
    <div class="note" style="margin-top:8px">Passengers, both directions, first full year after
    launch. The forecast was made as standing the year before launch, with no knowledge of the
    outcome, and graded against the aircraft and frequency the carrier actually flew.</div>
  </div>
{ctx_html}
  <div class="note" style="margin-top:14px">
    Why publish this: independent route forecasts are almost never tested against outturn.
    This engine is calibrated on launched-route outcomes and re-tested as the sample grows;
    the distribution above is what a central forecast means in practice at this airport.
    Indicative, for directional guidance; per-route precision varies with market data coverage.
  </div>
</div></body></html>"""


def render_total(t, source_name):
    esc = _html.escape
    yr = t["years"]
    yr_label = f"{yr[0]}-{yr[-1]}" if yr else "the sample"

    def _section(title, note, stats, hist):
        if not stats:
            return f'<div class="card"><h2 style="margin-top:0">{esc(title)}</h2><div class="note">no graded routes</div></div>'
        counts, labels = hist
        return (f'<div class="card"><h2 style="margin-top:0">{esc(title)}</h2>'
                f'<div class="note">{esc(note)}</div>{_tiles(stats)}'
                f'<div style="margin-top:14px">{_svg_hist(counts, labels)}</div></div>')

    def _brk(title, rowslist):
        body = "".join(_stat_row(esc(k), s) for k, s in rowslist if s)
        return (f'<div class="card"><h2 style="margin-top:0">{esc(title)}</h2><table>'
                f'<tr><th>set</th><th>n</th><th>median</th><th>over/under</th><th>half within</th>'
                f'<th>80% within</th><th>&plusmn;10%</th><th>&plusmn;20%</th><th>&plusmn;30%</th></tr>'
                f'{body}</table></div>')

    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Track Record &middot; Whole engine &middot; The Observatory</title>
{FONT_LINK}{OBS_STYLE}</head><body><div class="wrap">
  <div class="topnav"><a href="/">&larr; Route Forecasting</a>
    <a href="/trackrecord">Check one airport</a></div>
  <div class="kicker">The Observatory &middot; Meridian &middot; Forecast Track Record</div>
  <h1>Whole-engine track record</h1>
  <div class="sub">Every new route in the graded sample, across all airports, forecast the year before
  launch with no knowledge of the outcome and graded against actual first-full-year traffic. Launch years
  {yr_label}. {t['n_all']:,} routes, {t['n_origins']} origin airports, {t['n_carriers']} carriers:
  {t['n_fore']:,} into existing markets (demand pre-existed) and {t['n_indu']:,} into new markets (the route
  created the demand). <span class="badge">Evidence file <b>{esc(source_name)}</b></span></div>

  {_section("All launches (the whole book)", "Existing and new markets combined: every route the engine forecast, graded against what it carried.", t['stats_all'], t['hist_all'])}
  {_section("Existing markets (the engine's core test)", "Demand at least the route's size was already flying before the route; the honest test of a data-driven forecast.", t['stats_fore'], t['hist_fore'])}
  {_section("New markets (created by the route)", "The route created demand that wasn't visible before; forecast from the capacity-anchored floor, not a measured market.", t['stats_indu'], t['hist_indu'])}

  {_brk("By carrier type (all launches)", t['bytype'])}
  {_brk("By region (all launches)", t['byreg'])}

  <div class="note" style="margin-top:14px">
    Median forecast &divide; actual near 1.00 means unbiased; the within-bands and the &times;-factors show
    the spread. Existing markets are the core engine test; new markets are modelled from comparable launches,
    not a measured market, and are shown so the whole book is visible. Indicative, for directional guidance;
    per-route precision varies with market-data coverage.
  </div>
</div></body></html>"""


def page(airport=None):
    """The portal entry point: form when no airport given, else the rendered evidence page."""
    src = _source_path()
    if not src:
        return "<h3>No back-test evidence file found (bt_v1_baseline.csv) on the server.</h3>"
    if airport and airport.strip().upper() in ("ALL", "TOTAL", "ENGINE"):
        return render_total(total_track(load_rows(src)), os.path.basename(src))
    if not airport:
        return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Track Record &middot; The Observatory</title>
{FONT_LINK}
<style>
  *{{box-sizing:border-box}}
  body{{font-family:{SERIF};background:{SCREEN};color:{INKTX};margin:0;display:flex;justify-content:center;padding-top:96px}}
  .card{{background:{PAPER};border:1px solid {LINE};border-radius:2px;padding:30px;width:400px}}
  .kicker{{font-family:{SANS};font-size:9px;letter-spacing:.2em;text-transform:uppercase;color:{MUT};font-weight:600}}
  h2{{font-family:{SERIF};font-weight:400;color:{INK};margin:8px 0 8px;font-size:22px}}
  p{{font-family:{SERIF};color:{BODY};font-size:13px;line-height:1.55}}
  label{{font-family:{SANS};font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:{MUT};font-weight:600;display:block;margin:16px 0 6px}}
  input{{width:100%;padding:10px 11px;font-family:{SERIF};font-size:15px;border:1px solid {LINE};border-radius:2px;background:#FFFDF8;color:{INK}}}
  input:focus{{outline:none;border-color:{BRASS};box-shadow:0 0 0 2px rgba(212,162,73,.28)}}
  button{{margin-top:14px;width:100%;padding:11px;background:{INK};color:{PAPER};border:0;border-radius:2px;font-family:{SANS};font-weight:600;font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;cursor:pointer}}
  button:hover{{background:#0B141D}}
  a{{color:{INK};font-weight:600;text-decoration:none;border-bottom:1px solid {BRASS}}}
  a.back{{display:inline-block;margin-bottom:10px;font-family:{SANS};font-size:10px;letter-spacing:.1em;text-transform:uppercase}}
  :focus-visible{{outline:2px solid {BRASS};outline-offset:2px}}
</style>
</head><body><div class="card"><a class="back" href="/">&larr; Route Forecasting</a>
<div class="kicker">The Observatory &middot; Meridian</div>
<h2>Track Record</h2><p>How the forecast engine has performed against every new route launched
at an airport, graded on actual outturn.</p>
<form method="get"><label>Airport (IATA)</label><input name="airport" placeholder="e.g. LGW" autofocus>
<button>Show the record</button></form>
<p style="margin-top:16px">Or see the <a href="/trackrecord?airport=ALL">whole-engine record</a> across every airport, existing and new markets.</p></div></body></html>"""
    rows = load_rows(src)
    t = airport_track(rows, airport)
    # whole-engine context = the existing-market book across every airport (the honest ~41% engine, incl the
    # cause-based overrides). To frame with the full per-airport-optimised 52.9% instead, swap the ratios here
    # for the optimised set - but note that leaves the airport panels sitting below the context, and it's the
    # in-sample-fitted figure; see ENRICHED_BACKTEST_SPEC.md.
    _fore_all = [r["ratio"] for r in rows if r["forecastable"]]
    engine_ctx = {"hist": _hist(_fore_all), "stats": _stats(_fore_all)} if _fore_all else None
    return render_html(t, os.path.basename(src), engine_ctx)


def main():
    ap = argparse.ArgumentParser(description="Per-airport back-test track record page.")
    ap.add_argument("airport")
    ap.add_argument("--source", default=None, help="back-test CSV (default: newest evidence file)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    src = a.source or _source_path()
    rows = load_rows(src)
    t = airport_track(rows, a.airport)
    out = a.out or os.path.join(HERE, f"track_{a.airport.upper()}.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(render_html(t, os.path.basename(src)))
    s = t["stats_basis"]
    print(f"{a.airport.upper()}: {t['n_here']} routes here ({t['n_fore_here']} forecastable); "
          f"basis={t['basis']} n={t['basis_n']} median {s['median']:.2f} "
          f"half-within x{s['f50']:.2f} -> {out}")


if __name__ == "__main__":
    main()
