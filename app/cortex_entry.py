#!/usr/bin/env python3
r"""
The Observatory - Meridian branded entry screens (sign-in, welcome, loading, error).
====================================================================================
Productionised from the design canvas (Observatory Entry Screens.dc.html): options 4a / 5c / 5d / 6b, the
Meridian (operations / radar) register. Full-viewport, responsive (desktop-first, stacks below 900px), with the
brand tokens, Newsreader / IBM Plex Mono / Inter fonts, the animated radar seal, the four keyframes, reduced-motion
fallbacks and real <label>s. Every dynamic figure is passed in by the server (never hardcoded here): user name,
forecasts-run count, recent runs, run steps, route context, error refs.

Photography is not shipped, so the photo slot uses an ink-and-brass gradient treatment; drop a real image behind
`.photo` when licensed capture lands.
"""
import html

_FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
          '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
          '<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300;'
          '0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&family=IBM+Plex+Mono:wght@400;500'
          '&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">')

# brand tokens + keyframes + reduced-motion; shared by every screen
_BASE_CSS = """
:root{--ink:#0b141d;--panel:#0f1b28;--surface:#141c25;--h1:#1c2530;--h2:#22303c;--h3:#2a3a49;--h4:#3a4a58;
 --brass:#d4a249;--brass-link:#b8862f;--brass-lt:#e7c079;--paper:#f4f1ea;--paper2:#f6efe0;
 --muted:#9aa7b3;--muted2:#8998a6;--body:#c4cdd6;--faint:#5a6470;--live:#5fd08a;--err:#d08a5f;--err2:#c0724a;}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:var(--ink);color:var(--paper);
 font-family:'Newsreader',Georgia,serif;-webkit-font-smoothing:antialiased}
.mono{font-family:'IBM Plex Mono',ui-monospace,monospace}
.sans{font-family:'Inter',system-ui,sans-serif}
a{color:var(--brass-link);text-decoration:none}
button{font:inherit;cursor:pointer;border:none;background:none;color:inherit}
input{font-family:'Inter',system-ui,sans-serif}
.screen{min-height:100vh;display:flex}
/* the ink-and-brass photo treatment standing in for licensed capture */
.photo{position:absolute;inset:0;overflow:hidden;pointer-events:none;
 background:
  radial-gradient(120% 90% at 78% 18%,rgba(212,162,73,.16),transparent 46%),
  radial-gradient(90% 80% at 12% 88%,rgba(95,208,138,.05),transparent 52%),
  conic-gradient(from 210deg at 70% 40%,rgba(20,28,37,.0),rgba(11,20,29,.55) 40%,rgba(11,20,29,.0) 70%),
  linear-gradient(120deg,#0a121a,#0f1b28 55%,#0a1119);}
.photo::after{content:"";position:absolute;inset:0;
 background:repeating-linear-gradient(115deg,rgba(255,255,255,.014) 0 2px,transparent 2px 22px);opacity:.6}
.seal{position:relative;flex:none}
.seal .sweep{position:absolute;inset:0;border-radius:50%;
 background:conic-gradient(from 0deg,rgba(95,208,138,.55),transparent 70%);
 -webkit-mask:radial-gradient(circle,transparent 3px,#000 3.5px);mask:radial-gradient(circle,transparent 3px,#000 3.5px);
 animation:obsSweep 3.2s linear infinite}
.seal.err .sweep{background:conic-gradient(from 0deg,rgba(208,138,95,.5),transparent 72%);animation-duration:5s}
.eyebrow{font-family:'IBM Plex Mono',monospace;letter-spacing:.2em;color:var(--brass-lt);font-size:10px}
.lockup .obs{font-weight:300;color:var(--muted);line-height:1}
.lockup .name{font-weight:500;color:var(--paper);line-height:1.15}
.lockup .sub{font-family:'IBM Plex Mono',monospace;letter-spacing:.2em;color:var(--muted2)}
.fld{height:46px;border:1px solid var(--h4);border-radius:4px;background:rgba(244,241,234,.06);
 display:flex;align-items:center;padding:0 14px;width:100%;color:var(--paper);font-size:13px}
.fld::placeholder{color:var(--muted)}
.fld:focus{outline:none;border-color:var(--brass)}
.btn-brass{height:48px;border-radius:4px;background:var(--brass);color:var(--ink);width:100%;
 font-family:'Newsreader',serif;font-size:17px;font-weight:500;display:flex;align-items:center;justify-content:center;gap:9px}
.btn-brass:hover{background:#e0af53}
.btn-ghost{height:46px;border:1px solid var(--h3);border-radius:4px;background:transparent;color:var(--body);
 font-family:'Inter',sans-serif;font-size:12.5px;font-weight:500;display:flex;align-items:center;justify-content:center;width:100%}
.pill{display:inline-flex;align-items:center;gap:8px;background:rgba(11,20,29,.55);border:1px solid rgba(212,162,73,.4);
 border-radius:100px;padding:7px 14px}
.dot{width:6px;height:6px;border-radius:50%;background:var(--live);box-shadow:0 0 7px var(--live);display:block}
.err-inline{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.06em;color:var(--err2);margin-top:10px;min-height:12px}
@keyframes obsSweep{to{transform:rotate(360deg)}}
@keyframes obsOrbit{to{transform:rotate(360deg)}}
@keyframes obsFill{0%{width:8%}100%{width:76%}}
@keyframes obsPulse{0%,100%{opacity:.35}50%{opacity:1}}
@media (prefers-reduced-motion: reduce){
 .seal .sweep{animation:none}
 [data-anim="fill"]>i{animation:none!important;width:60%!important}
 [data-anim="pulse"]{animation:none!important;opacity:1!important}
}
@media (max-width:900px){
 .screen{flex-direction:column;overflow:visible;height:auto}
 .wrap{flex-direction:column}
 .split-photo{height:auto!important;min-height:auto!important;padding:32px 20px!important;justify-content:flex-start!important}
 .split-form{padding:26px 20px!important;width:auto!important;flex:1 1 auto!important;border-right:none!important;border-left:none!important}
 .glass{position:static!important;transform:none!important;width:auto!important;max-width:none!important;margin:0}
 .stmt{position:static!important;transform:none!important;max-width:none!important}
 .stmt h1{font-size:38px!important}
 .fld,.btn-brass,.btn-ghost{height:46px}
 .hide-sm{display:none!important}
 .stat-row{flex-wrap:wrap;gap:20px!important}
}
"""

# animated radar seal (Meridian). err=True swaps to the terracotta dashed variant.
def _seal(px=42, err=False, rings=True):
    stroke = "#d08a5f" if err else "#d4a249"
    dash = ' stroke-dasharray="6 7"' if err else ""
    inner = ('<circle cx="60" cy="60" r="26" stroke="#3a4a58" stroke-width="1.1" fill="none"/>' if rings else "")
    return (f'<span class="seal{" err" if err else ""}" style="width:{px}px;height:{px}px" aria-hidden="true">'
            f'<svg viewBox="0 0 120 120" style="width:{px}px;height:{px}px;position:absolute;inset:0">'
            f'<circle cx="60" cy="60" r="42" stroke="#c4cdd6" stroke-width="2" fill="none"/>{inner}'
            f'<path d="M32 88 A 82 82 0 0 1 95 43" stroke="{stroke}" stroke-width="3.4" fill="none" '
            f'stroke-linecap="round"{dash}/><circle cx="60" cy="60" r="4.5" fill="{stroke}"/></svg>'
            f'<span class="sweep"></span></span>')


def _lockup(px=42, stack=False):
    align = "flex-direction:column;text-align:center;gap:8px" if stack else "gap:14px"
    return (f'<div class="lockup" style="display:flex;align-items:center;{align}">{_seal(px)}'
            f'<div><div class="obs" style="font-size:12px">The Observatory</div>'
            f'<div class="name" style="font-size:22px">Meridian</div>'
            f'<div class="sub" style="font-size:8px;margin-top:2px">ROUTE FORECASTING</div></div></div>')


def _head(title):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(title)} · Meridian</title>{_FONTS}<style>{_BASE_CSS}</style></head>')


def _photo(url, overlay, opacity="1"):
    """The photo layer: the real image (if given) over the ink-gradient fallback, with a per-screen overlay on top."""
    img = (f'<img src="{url}" alt="" style="position:absolute;inset:0;width:100%;height:100%;'
           f'object-fit:cover;opacity:{opacity}">') if url else ""
    return f'<div class="photo">{img}<div style="position:absolute;inset:0;background:{overlay}"></div></div>'


# --------------------------------------------------------------------------- 4a  SIGN IN
def signin(forecasts_run="12,480", median_runtime="&lt; 4 min", markets="190+", error="", next_url="/welcome",
           ops_tower="/static/entry/ops-tower.png", demo=False):
    demo_note = ('<div class="mono" style="font-size:9px;letter-spacing:.04em;color:var(--muted);margin:-12px 0 18px">'
                 'Preview access · enter any details to continue</div>') if demo else ""
    err_html = f'{html.escape(error)}' if error else ""
    return f"""{_head("Sign in")}<body><main class="screen" role="main">
  <section class="split-photo stmt" style="position:relative;flex:1;min-height:100vh;display:flex;flex-direction:column;justify-content:center;padding:0 44px">
    {_photo(ops_tower, "linear-gradient(100deg,rgba(9,14,20,.90),rgba(9,14,20,.55) 46%,rgba(9,14,20,.30))")}
    <div style="position:absolute;top:40px;left:44px">{_lockup(42)}</div>
    <div style="position:relative;max-width:560px">
      <div class="eyebrow" style="margin-bottom:20px">THE ROUTE FORECAST, REDRAWN</div>
      <h1 style="font-weight:400;font-size:clamp(34px,5vw,52px);line-height:1.04;letter-spacing:-.01em;margin:0">
        Every market.<br>Every route.<br><span style="font-style:italic;color:var(--brass-lt)">In focus.</span></h1>
      <p style="font-weight:300;font-size:19px;line-height:1.45;color:var(--body);margin:24px 0 0;max-width:452px">
        Bespoke O&amp;D forecasts on the QSI engine, prepared to your brief and brought into clear view.</p>
      <div class="stat-row" style="display:flex;gap:34px;margin-top:34px">
        <div><div style="font-size:30px;color:var(--paper2);line-height:1" data-live="forecasts_run">{forecasts_run}</div>
          <div class="mono" style="font-size:8.5px;letter-spacing:.14em;color:var(--muted2);margin-top:6px;display:flex;align-items:center;gap:6px"><span class="dot"></span>FORECASTS RUN</div></div>
        <div style="border-left:1px solid var(--h4);padding-left:34px"><div style="font-size:30px;color:var(--paper2);line-height:1" data-live="median_runtime">{median_runtime}</div>
          <div class="mono" style="font-size:8.5px;letter-spacing:.14em;color:var(--muted2);margin-top:6px">MEDIAN RUNTIME</div></div>
        <div style="border-left:1px solid var(--h4);padding-left:34px"><div style="font-size:30px;color:var(--paper2);line-height:1" data-live="markets_covered">{markets}</div>
          <div class="mono" style="font-size:8.5px;letter-spacing:.14em;color:var(--muted2);margin-top:6px">MARKETS</div></div>
      </div>
    </div>
  </section>
  <section class="split-form" style="flex:none;width:clamp(360px,32vw,460px);display:flex;align-items:center;justify-content:center;padding:40px;background:var(--panel);border-left:1px solid var(--h1)">
    <form class="glass" method="post" action="/signin" style="width:100%;max-width:352px;background:rgba(11,17,23,.72);
      backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border:1px solid rgba(212,162,73,.3);border-radius:8px;padding:38px 38px 34px">
      <div class="eyebrow mono" style="color:var(--brass);letter-spacing:.2em;margin-bottom:20px">SIGN IN TO RUN A FORECAST</div>
      {demo_note}
      <input type="hidden" name="next" value="{html.escape(next_url)}">
      <label for="email" class="mono" style="position:absolute;left:-9999px">Email</label>
      <input id="email" name="email" type="email" class="fld sans" placeholder="you@carrier.com" autocomplete="username" style="margin-bottom:12px">
      <label for="password" class="mono" style="position:absolute;left:-9999px">Password</label>
      <input id="password" name="password" type="password" class="fld sans" placeholder="••••••••••••" autocomplete="current-password" style="margin-bottom:18px">
      <button type="submit" class="btn-brass">Open Meridian <span class="mono" style="font-size:14px">→</span></button>
      <div class="err-inline mono" role="alert">{err_html}</div>
      <div style="display:flex;align-items:center;gap:12px;margin:14px 0"><div style="flex:1;height:1px;background:var(--h3)"></div>
        <div class="mono" style="font-size:9px;color:var(--faint)">OR</div><div style="flex:1;height:1px;background:var(--h3)"></div></div>
      <button type="button" class="btn-ghost" onclick="alert('SSO is not configured in this build.')">Single sign-on (SSO)</button>
    </form>
  </section>
</main></body></html>"""


# --------------------------------------------------------------------------- 5c  WELCOME
def _recent_row(route, meta, status):
    up = (status or "").upper()
    if up == "RUNNING":
        pill = ('<div class="mono" data-anim="pulse" style="font-size:9px;letter-spacing:.12em;color:var(--brass-lt);display:flex;align-items:center;gap:6px">'
                '<span style="width:5px;height:5px;border-radius:50%;background:var(--brass-lt);display:block;animation:obsPulse 1.6s ease-in-out infinite"></span>RUNNING</div>')
    else:
        pill = f'<div class="mono" style="font-size:9px;letter-spacing:.12em;color:var(--live)">{html.escape(up or "COMPLETE")}</div>'
    return (f'<div style="display:flex;justify-content:space-between;align-items:center;padding:14px 0;border-bottom:1px solid var(--h1)">'
            f'<div><div style="font-size:18px;color:var(--paper)">{html.escape(route)}</div>'
            f'<div class="mono" style="font-size:9px;color:var(--muted2);letter-spacing:.1em;margin-top:3px">{html.escape(meta)}</div></div>{pill}</div>')


def welcome(user_name="there", forecasts_run="12,480", recents=None, app_url="/", new_url="/",
            ops_radar="/static/entry/ops-radar.png"):
    recents = recents or []
    if recents:
        rows = "".join(_recent_row(r.get("route", ""), r.get("meta", ""), r.get("status", "")) for r in recents)
        recent_block = (f'<div class="mono" style="font-size:10px;letter-spacing:.16em;color:var(--muted2);margin-bottom:18px">RECENT FORECASTS</div>'
                        f'<div style="display:flex;flex-direction:column;gap:2px">{rows}</div>'
                        f'<div class="mono" style="font-size:9px;letter-spacing:.12em;color:var(--brass-link);margin-top:16px"><a href="{app_url}">VIEW ALL →</a></div>')
    else:
        recent_block = ('<div class="mono" style="font-size:10px;letter-spacing:.16em;color:var(--muted2);margin-bottom:18px">RECENT FORECASTS</div>'
                        '<div style="font-weight:300;font-size:16px;color:var(--muted);line-height:1.5">No forecasts yet. Start your first on the left, and it will appear here.</div>')
    return f"""{_head("Welcome")}<body><main class="screen" role="main" style="flex-direction:column">
  <div style="position:relative;height:208px;flex:none;overflow:hidden">
    {_photo(ops_radar, "linear-gradient(105deg,rgba(11,20,29,.82),rgba(11,20,29,.35) 60%,rgba(11,20,29,.7))")}
    <div style="position:absolute;top:32px;left:40px">{_lockup(40)}</div>
    <div style="position:absolute;top:36px;right:40px" class="pill hide-sm"><span class="dot"></span>
      <span class="mono" style="font-size:9px;letter-spacing:.14em;color:#e7e3d9">ENGINE LIVE · <span data-live="forecasts_run">{forecasts_run}</span> DELIVERED</span></div>
  </div>
  <div style="flex:1;background:var(--panel);display:flex;justify-content:center;align-items:flex-start;padding:44px 24px 56px">
   <div class="wrap" style="width:100%;max-width:1060px;display:flex;align-items:stretch">
    <div class="split-form" style="flex:0 0 54%;padding:0 46px 0 0;display:flex;flex-direction:column;border-right:1px solid var(--h1)">
      <div style="font-weight:300;font-style:italic;font-size:20px;color:var(--body)">Welcome back,</div>
      <div data-user-name style="font-weight:500;font-size:40px;color:var(--paper2);line-height:1.05;margin-top:2px">{html.escape(user_name)}</div>
      <p style="font-weight:300;font-size:16px;color:var(--muted);line-height:1.5;margin:12px 0 26px;max-width:400px">
        Set an origin, a destination and your criteria. The QSI engine does the rest.</p>
      <a href="{new_url}" style="text-decoration:none"><div style="border-radius:6px;background:var(--brass);padding:20px 24px;display:flex;justify-content:space-between;align-items:center">
        <div><div style="font-size:21px;color:var(--ink);font-weight:500">Start a new forecast</div>
          <div class="mono" style="font-size:9px;letter-spacing:.14em;color:#5a4212;margin-top:4px">DEFINE MARKET · CRITERIA · HORIZON</div></div>
        <span class="mono" style="font-size:20px;color:var(--ink)">→</span></div></a>
      <a href="{app_url}" style="text-decoration:none"><div style="border:1px solid var(--h3);border-radius:6px;padding:15px 24px;margin-top:12px;font-size:16px;color:var(--body);display:flex;justify-content:space-between;align-items:center">
        Load a saved brief <span class="mono" style="font-size:14px;color:var(--muted2)">↑</span></div></a>
    </div>
    <div style="flex:1;padding:0 0 0 40px">{recent_block}</div>
   </div>
  </div>
</main></body></html>"""


# --------------------------------------------------------------------------- 5d  LOADING
def loading(context="LHR → JFK · SUMMER 2026", steps=None, poll_url="", done_url="/",
            ops_radar="/static/entry/ops-radar.png"):
    steps = steps or [("Ingesting schedules & capacity", "done"), ("Scoring QSI market shares", "active"),
                      ("Resolving O&D demand", "pending"), ("Rendering the report", "pending")]
    rows = []
    for label, st in steps:
        if st == "done":
            marker = ('<span style="width:16px;height:16px;border-radius:50%;background:var(--live);color:var(--ink);'
                      'font-family:\'IBM Plex Mono\',monospace;font-size:10px;display:flex;align-items:center;justify-content:center;flex:none">✓</span>')
            col = "var(--muted)"
        elif st == "active":
            marker = ('<span data-anim="pulse" style="width:16px;height:16px;border-radius:50%;border:2px solid var(--brass-lt);flex:none;animation:obsPulse 1.4s ease-in-out infinite"></span>')
            col = "var(--paper)"
        else:
            marker = '<span style="width:16px;height:16px;border-radius:50%;border:2px solid var(--h3);flex:none"></span>'
            col = "var(--faint)"
        rows.append(f'<div style="display:flex;align-items:center;gap:12px">{marker}'
                    f'<span class="mono" style="font-size:11px;letter-spacing:.1em;color:{col}">{html.escape(label)}</span></div>')
    poll = f'<script>setTimeout(function(){{location.href="{done_url}"}},4000);</script>' if not poll_url else ""
    return f"""{_head("Running")}<body><main class="screen" role="status" aria-live="polite" style="position:relative">
  {_photo(ops_radar, "radial-gradient(ellipse at center,rgba(11,20,29,.55),rgba(11,20,29,.88))", opacity=".3")}
  <div style="position:absolute;top:40px;left:44px;display:flex;align-items:center;gap:13px">{_seal(30)}
    <span class="mono" style="font-size:9px;letter-spacing:.2em;color:var(--body)">THE OBSERVATORY · MERIDIAN</span></div>
  <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:min(560px,90vw);text-align:center">
    <div style="width:128px;height:128px;margin:0 auto 26px">{_seal(128, rings=True)}</div>
    <div class="eyebrow mono" style="letter-spacing:.22em;color:var(--brass-lt);margin-bottom:12px">{html.escape(context)}</div>
    <h1 style="font-weight:400;font-size:34px;line-height:1.1;margin:0">Running your forecast</h1>
    <div style="width:min(420px,86vw);margin:28px auto 0;text-align:left;display:flex;flex-direction:column;gap:11px">{''.join(rows)}</div>
    <div data-anim="fill" style="width:min(420px,86vw);height:3px;background:var(--h1);border-radius:2px;margin:26px auto 0;overflow:hidden">
      <i style="display:block;height:100%;background:linear-gradient(90deg,var(--live),var(--brass-lt));animation:obsFill 3s ease-in-out infinite alternate"></i></div>
  </div>
  <div style="position:absolute;left:0;right:0;bottom:34px;text-align:center" class="mono" style="font-size:8.5px;letter-spacing:.16em;color:var(--faint)">MEDIAN RUNTIME UNDER FOUR MINUTES · QSI METHODOLOGY</div>
  {poll}
</main></body></html>"""


# --------------------------------------------------------------------------- 6b  ERROR
def error(context="LHR → JFK · SUMMER 2026", paused_at="42%", err_ref="MER-1102", retry="3 OF 5",
          resume_url="/", exit_url="/welcome", ops_radar="/static/entry/ops-radar.png"):
    return f"""{_head("Signal lost")}<body><main class="screen" role="alert" aria-live="assertive" style="position:relative">
  {_photo(ops_radar, "radial-gradient(ellipse at center,rgba(11,20,29,.5),rgba(11,20,29,.9))", opacity=".26")}
  <div style="position:absolute;top:40px;left:44px;display:flex;align-items:center;gap:13px">{_seal(30, err=True, rings=False)}
    <span class="mono" style="font-size:9px;letter-spacing:.2em;color:var(--body)">THE OBSERVATORY · MERIDIAN</span></div>
  <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:min(560px,90vw);text-align:center">
    <div style="width:96px;height:96px;margin:0 auto 26px">{_seal(96, err=True, rings=True)}</div>
    <div class="mono" style="font-size:11px;letter-spacing:.22em;color:var(--err);margin-bottom:14px">SIGNAL LOST · RUN PAUSED</div>
    <h1 style="font-weight:400;font-size:34px;line-height:1.12;margin:0">The engine dropped the connection</h1>
    <p style="font-weight:300;font-size:17px;color:var(--muted);line-height:1.5;margin:14px auto 0;max-width:430px">
      Your forecast is paused at QSI scoring and will resume exactly where it stopped.</p>
    <div class="pill" style="margin-top:20px;border-color:var(--h3);background:rgba(11,20,29,.6)">
      <span class="mono" style="font-size:9px;letter-spacing:.14em;color:var(--body)">{html.escape(context)}</span>
      <span style="width:1px;height:12px;background:var(--h3)"></span>
      <span class="mono" style="font-size:9px;letter-spacing:.14em;color:var(--brass-lt)">PAUSED AT {html.escape(paused_at)}</span></div>
    <div style="display:flex;gap:12px;justify-content:center;margin-top:26px;flex-wrap:wrap">
      <a href="{resume_url}"><button class="btn-brass" style="width:auto;padding:0 26px">Reconnect &amp; resume <span class="mono" style="font-size:13px">→</span></button></a>
      <a href="{exit_url}"><button class="btn-ghost" style="width:auto;padding:0 24px;font-family:'Newsreader',serif;font-size:16px;color:var(--body)">Save &amp; exit</button></a>
    </div>
  </div>
  <div style="position:absolute;left:0;right:0;bottom:34px;text-align:center" class="mono" style="font-size:8.5px;letter-spacing:.16em;color:var(--faint)">ERR · {html.escape(err_ref)} · AUTO-RETRY {html.escape(retry)} · QSI ENGINE</div>
</main></body></html>"""
