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
SOURCES = ["bt_v2_6yr.csv", "bt_v1_6yr.csv", "bt_v1_baseline.csv"]
FLOOR = 15        # min forecastable routes for airport-only stats
PEER_MIN = 30     # min for peer-group stats before falling back to global

NAVY, ACCENT, MUT, BG = "#0b2545", "#1f6feb", "#5b6b7c", "#f5f7fa"


def _source_path():
    for s in SOURCES:
        p = os.path.join(HERE, s)
        if os.path.exists(p):
            return p
    return None


def load_rows(path):
    rows = []
    for r in csv.DictReader(open(path)):
        try:
            ratio = float(r.get("fc_over_out") or 0)
            if ratio <= 0:
                continue
            rows.append({
                "route": r["route"], "dep": r["dep"], "arr": r["arr"],
                "year": int(r["year"]), "region": r.get("region", ""),
                "carrier": r.get("carrier", ""), "type": r.get("type", ""),
                "ratio": ratio,
                "forecast": float(r.get("forecast_pax") or 0),
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
    """The bell curve, labelled for a reader with no statistics: each bar counts routes by how
    far the forecast landed from the actual outcome; a shaded centre band marks 'within 20%'."""
    mx = max(counts) or 1
    W, H, pad, top = 760, 250, 30, 30
    bw = (W - 2 * pad) / len(counts)
    plot_h = H - pad - 44 - top
    n = len(counts)
    # the 'within +/-20%' band in log2 units mapped to x
    span = 6.0                                  # -3..+3 log2
    bx = lambda v: pad + (v + 3.0) / span * (W - 2 * pad)
    b20l, b20r = bx(-math.log2(1.2)), bx(math.log2(1.2))
    bars, ticks = [], []
    for i, c in enumerate(counts):
        h = plot_h * c / mx
        x = pad + i * bw
        mid = i == n // 2
        bars.append(f'<rect x="{x+2:.0f}" y="{H-44-h:.0f}" width="{bw-4:.0f}" height="{h:.0f}" '
                    f'rx="3" fill="{ACCENT if mid else NAVY}" opacity="{1.0 if mid else 0.82}"/>')
        if c:
            bars.append(f'<text x="{x+bw/2:.0f}" y="{H-44-h-5:.0f}" text-anchor="middle" '
                        f'font-size="10" fill="{MUT}">{c}</text>')
        if i % 2 == 0:
            ticks.append(f'<text x="{x+bw/2:.0f}" y="{H-30}" text-anchor="middle" font-size="9.5" '
                         f'fill="{MUT}">{labels[i]}</text>')
    return (f'<svg viewBox="0 0 {W} {H}" style="width:100%;max-width:{W}px">'
            # shaded 'about right' band behind the bars
            f'<rect x="{b20l:.0f}" y="{top}" width="{b20r-b20l:.0f}" height="{H-44-top}" '
            f'fill="{ACCENT}" opacity="0.08"/>'
            f'<line x1="{bx(0):.0f}" y1="{top}" x2="{bx(0):.0f}" y2="{H-44}" '
            f'stroke="{ACCENT}" stroke-dasharray="4 3" opacity="0.6"/>'
            f'<line x1="{pad}" y1="{H-44}" x2="{W-pad}" y2="{H-44}" stroke="#d7dee7"/>'
            + "".join(bars) + "".join(ticks) +
            f'<text x="{W/2:.0f}" y="14" text-anchor="middle" font-size="12" fill="{NAVY}" '
            f'font-weight="600">Each bar counts routes by how the forecast compared with what '
            f'the route actually carried</text>'
            f'<text x="{pad}" y="{H-6}" font-size="10.5" fill="{MUT}">&#8592; forecast came in '
            f'LOW (route did better than forecast)</text>'
            f'<text x="{bx(0):.0f}" y="{H-6}" text-anchor="middle" font-size="10.5" '
            f'fill="{ACCENT}" font-weight="600">on the money</text>'
            f'<text x="{W-pad}" y="{H-6}" text-anchor="end" font-size="10.5" fill="{MUT}">'
            f'forecast came in HIGH (route did worse) &#8594;</text></svg>'
            f'<div class="note" style="margin-top:6px">How to read it: a route in the shaded '
            f'centre band was forecast within 20% of its actual first-year traffic. "x2.0" '
            f'means the forecast was double what the route carried; "1/2.0" means the route '
            f'carried double the forecast. The tighter the bars cluster on the centre, the '
            f'more dependable the forecast.</div>')


def render_html(t, source_name):
    a = t["airport"]
    name = _apt_name(a)
    yrs = t["years"]
    yr_label = f"{min(yrs)}-{max(yrs)}" if yrs else "-"
    basis_note = {
        "airport": f"Statistics are for the {t['basis_n']} forecastable routes at {a} itself.",
        "peer": (f"{a} has {t['n_fore_here']} forecastable launches in the sample - too few for "
                 f"a distribution of its own - so the headline statistics use the {t['basis_n']} "
                 f"forecastable routes in its peer group ({', '.join(t['regions']) or 'same region'}). "
                 f"{a}'s own routes are shown separately below."),
        "global": (f"{a} has {t['n_fore_here']} forecastable launches in the sample - too few for "
                   f"a distribution - so the headline statistics use the full forecastable sample. "
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

    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Track record - {esc(a)} - Avia Cortex</title>
<style>
  body{{font-family:Segoe UI,system-ui,-apple-system,sans-serif;background:{BG};color:#17222e;margin:0}}
  .wrap{{max-width:900px;margin:0 auto;padding:26px 18px 60px}}
  h1{{color:{NAVY};font-size:24px;margin:6px 0 2px}} h2{{color:{NAVY};font-size:16px;margin:26px 0 8px}}
  .sub{{color:{MUT};font-size:13px}} .note{{color:{MUT};font-size:12.5px;line-height:1.5}}
  .card{{background:#fff;border:1px solid #e3e9f0;border-radius:12px;padding:18px;margin-top:14px}}
  .tiles{{display:flex;gap:10px;flex-wrap:wrap;margin-top:6px}}
  .tile{{flex:1;min-width:130px;background:#fff;border:1px solid #e3e9f0;border-radius:12px;padding:12px}}
  .tv{{font-size:22px;font-weight:700;color:{NAVY}}} .tl{{font-size:11px;color:{MUT};margin-top:3px}}
  table{{border-collapse:collapse;width:100%;font-size:12.5px}}
  th{{text-align:left;color:{MUT};font-weight:600;padding:6px 8px;border-bottom:1.5px solid #e3e9f0}}
  td{{padding:6px 8px;border-bottom:1px solid #eef2f6}}
  .badge{{display:inline-block;background:{ACCENT}12;color:{ACCENT};border:1px solid {ACCENT}44;
         border-radius:99px;padding:2px 10px;font-size:11px;font-weight:600}}
  .topnav{{display:flex;gap:14px;align-items:center;margin-bottom:10px;font-size:12.5px}}
  .topnav a{{color:{ACCENT};text-decoration:none;font-weight:600}}
</style></head><body><div class="wrap">
  <div class="topnav"><a href="/">&larr; Route Forecasting</a>
    <a href="/trackrecord">Check another airport</a></div>
  <div class="sub">Avia Cortex &middot; forecast track record</div>
  <h1>{esc(name)} ({esc(a)})</h1>
  <div class="sub">Every new route launched at {esc(a)} in the graded sample, forecast the year
  before launch with no knowledge of the outcome, against the route's actual first-full-year
  traffic. Launch years {yr_label}. Of the {t['n_here']} launches here, {t['n_fore_here']} are
  <b>forecastable</b> (a market at least the route's size already existed) and {t['n_here']-t['n_fore_here']}
  are <b>induced</b> (the route created a market history did not show); the headline below is the
  forecastable set, the engine's real test, with induced listed separately lower down.
  <span class="badge">evidence file: {esc(source_name)}</span></div>

  <div class="card">
    <h2 style="margin-top:0">The engine's real test: forecastable routes</h2>
    <div class="note">{esc(basis_note)}</div>
    {_tiles(t['stats_basis'])}
    <div style="margin-top:14px">{_svg_hist(counts, labels)}</div>
  </div>

  <div class="card">
    <h2 style="margin-top:0">The detail</h2>
    <table>
      <tr><th>set</th><th>n</th><th>median</th><th>over/under</th><th>half within</th>
          <th>80% within</th><th>&plusmn;10%</th><th>&plusmn;20%</th><th>&plusmn;30%</th></tr>
      {_stat_row(f"forecastable ({'this airport' if t['basis']=='airport' else 'peer group' if t['basis']=='peer' else 'all airports'})", t['stats_basis'])}
      {_stat_row(f"forecastable at {esc(a)} only", t['stats_here']) if t['basis'] != 'airport' else ''}
      {_stat_row(f"induced at {esc(a)} (route created the market)", t['stats_induced'])}
    </table>
    <div class="note" style="margin-top:10px">
      Forecastable = a market at least the route's eventual size already existed in booking data;
      this is the honest test of a data-driven forecast. Induced = the route created a market
      history did not show; forecasting those is the stimulation and judgement layer, shown
      separately and not blended into the headline. Ratios are graded against the aircraft and
      frequency actually flown.</div>
  </div>

  <div class="card">
    <h2 style="margin-top:0">Routes at {esc(a)} in the sample ({t['n_here']}: {t['n_fore_here']} forecastable + {t['n_here']-t['n_fore_here']} induced, newest first)</h2>
    <table><tr><th>route</th><th>carrier</th><th>launched</th><th>class</th>
    <th style="text-align:right">forecast, year 1</th><th style="text-align:right">actually carried</th><th>how it landed</th></tr>
    {route_rows}</table>
    <div class="note" style="margin-top:8px">Passengers, both directions, first full year after
    launch. The forecast was made as standing the year before launch, with no knowledge of the
    outcome, and graded against the aircraft and frequency the carrier actually flew.</div>
  </div>

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
<title>Track record - whole engine - Avia Cortex</title>
<style>
  body{{font-family:Segoe UI,system-ui,-apple-system,sans-serif;background:{BG};color:#17222e;margin:0}}
  .wrap{{max-width:900px;margin:0 auto;padding:26px 18px 60px}}
  h1{{color:{NAVY};font-size:24px;margin:6px 0 2px}} h2{{color:{NAVY};font-size:16px;margin:26px 0 8px}}
  .sub{{color:{MUT};font-size:13px}} .note{{color:{MUT};font-size:12.5px;line-height:1.5}}
  .card{{background:#fff;border:1px solid #e3e9f0;border-radius:12px;padding:18px;margin-top:14px}}
  .tiles{{display:flex;gap:10px;flex-wrap:wrap;margin-top:6px}}
  .tile{{flex:1;min-width:130px;background:#fff;border:1px solid #e3e9f0;border-radius:12px;padding:12px}}
  .tv{{font-size:22px;font-weight:700;color:{NAVY}}} .tl{{font-size:11px;color:{MUT};margin-top:3px}}
  table{{border-collapse:collapse;width:100%;font-size:12.5px}}
  th{{text-align:left;color:{MUT};font-weight:600;padding:6px 8px;border-bottom:1.5px solid #e3e9f0}}
  td{{padding:6px 8px;border-bottom:1px solid #eef2f6}}
  .badge{{display:inline-block;background:{ACCENT}12;color:{ACCENT};border:1px solid {ACCENT}44;
         border-radius:99px;padding:2px 10px;font-size:11px;font-weight:600}}
  .topnav{{display:flex;gap:14px;align-items:center;margin-bottom:10px;font-size:12.5px}}
  .topnav a{{color:{ACCENT};text-decoration:none;font-weight:600}}
</style></head><body><div class="wrap">
  <div class="topnav"><a href="/">&larr; Route Forecasting</a>
    <a href="/trackrecord">Check one airport</a></div>
  <div class="sub">Avia Cortex &middot; forecast track record</div>
  <h1>Whole-engine track record</h1>
  <div class="sub">Every new route in the graded sample, across all airports, forecast the year before
  launch with no knowledge of the outcome and graded against actual first-full-year traffic. Launch years
  {yr_label}. {t['n_all']:,} routes, {t['n_origins']} origin airports, {t['n_carriers']} carriers:
  {t['n_fore']:,} forecastable (a market pre-existed) and {t['n_indu']:,} induced (the route created the
  market). <span class="badge">evidence file: {esc(source_name)}</span></div>

  {_section("All launches (the whole book)", "Forecastable and induced combined: every route the engine forecast, graded against what it carried.", t['stats_all'], t['hist_all'])}
  {_section("Forecastable (the engine's core test)", "A market at least the route's size already existed in the booking data; the honest test of a measured-market forecast.", t['stats_fore'], t['hist_fore'])}
  {_section("Induced (new-market / stimulation layer)", "The route created a market history did not show; forecast from the capacity-anchored floor, not a measured market.", t['stats_indu'], t['hist_indu'])}

  {_brk("By carrier type (all launches)", t['bytype'])}
  {_brk("By region (all launches)", t['byreg'])}

  <div class="note" style="margin-top:14px">
    Median forecast &divide; actual near 1.00 means unbiased; the within-bands and the &times;-factors show
    the spread. Forecastable is the core engine test; induced is modelled from comparable launches, not a
    measured market, and is shown so the whole book is visible. Indicative, for directional guidance;
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
        return f"""<!doctype html><html><head><meta charset="utf-8"><title>Track record - Avia Cortex</title>
<style>body{{font-family:Segoe UI,system-ui,sans-serif;background:{BG};display:flex;justify-content:center;padding-top:80px}}
.card{{background:#fff;border:1px solid #e3e9f0;border-radius:12px;padding:28px;width:360px}}
h2{{color:{NAVY};margin:0 0 6px}} input{{width:100%;padding:10px;font-size:15px;border:1px solid #cfd8e3;border-radius:8px;box-sizing:border-box}}
button{{margin-top:10px;width:100%;padding:10px;background:{ACCENT};color:#fff;border:0;border-radius:8px;font-weight:600;font-size:14px;cursor:pointer}}
p{{color:{MUT};font-size:12.5px}}
a.back{{display:block;margin-bottom:10px;color:{ACCENT};text-decoration:none;font-weight:600;font-size:12.5px}}</style>
</head><body><div class="card"><a class="back" href="/">&larr; Route Forecasting</a>
<h2>Track record</h2><p>How the forecast engine has performed against every new route launched
at an airport, graded on actual outturn.</p>
<form method="get"><input name="airport" placeholder="Airport IATA, e.g. LGW" autofocus>
<button>Show the record</button></form>
<p style="margin-top:14px">Or see the <a href="/trackrecord?airport=ALL" style="color:{ACCENT};font-weight:600;text-decoration:none">whole-engine record</a> across every airport, forecastable and induced.</p></div></body></html>"""
    rows = load_rows(src)
    t = airport_track(rows, airport)
    return render_html(t, os.path.basename(src))


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
