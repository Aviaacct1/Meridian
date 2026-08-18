#!/usr/bin/env python3
"""
Avia Cortex - interactive HTML digital pitch (self-contained, emailable, iPad-friendly).
========================================================================================
build_html_pitch(fc, research_blocks, inputs) -> a single self-contained .html string: all CSS and
JS inline, all data embedded, no server calls and no CDN, so it opens offline on any laptop or iPad.
The route economics are LIVE (sliders recompute the P&L in the browser), the charts are hand-drawn
inline SVG, and the research is laid out as sourced cards rather than bullet lists. Photography is
embedded as base64 data URIs via inputs['images'] (hero, origin, destination) when supplied.

  fc              - the calibrated_forecast() dict (demand, capacity, economics{cost_model}, ...)
  research_blocks - {block_id: {"findings":[{claim, source_name, year, ...}], "summary": str}}
  inputs          - {airline_name, date, images:{hero,origin,dest}}  (images optional)
"""
import json


BLOCK_TITLES = {
    "economic_context": "Economic context", "corporate_links": "Corporate and technology links",
    "tourism": "Tourism and visitor economy", "trade": "Trade and investment",
    "airport_overview": "Airport", "diaspora": "Diaspora and VFR", "passenger_profile": "Passenger profile",
    "non_cannibalization": "Market stimulation", "case_study": "Comparable route", "education": "Education links",
}


def _n(v):
    try:
        return float(v or 0)
    except Exception:
        return 0.0


def build_html_pitch(fc, research_blocks=None, inputs=None):
    inputs = inputs or {}
    research_blocks = research_blocks or {}
    o = fc.get("origin", {}); d = fc.get("dest", {})
    dem = fc.get("demand", {}); cap = fc.get("capacity", {})
    ec = fc.get("economics", {}) or {}
    cm = ec.get("cost_model", {}) or {}
    airline = inputs.get("airline_name") or fc.get("airline") or "the airline"
    images = inputs.get("images", {}) or {}

    # connecting markets: full detail (base O&D, share, forecast, PDEW) for the charts and tables
    def _clist(key, n=15):
        out = []
        for r in (dem.get(key) or [])[:n]:
            out.append({"code": r.get("code"), "city": r.get("name") or r.get("code"),
                        "country": r.get("country") or "",
                        "base": round(_n(r.get("base"))), "share": _n(r.get("share")),
                        "pax": round(_n(r.get("forecast")) or _n(r.get("pdew")) * 365),
                        "pdew": round(_n(r.get("pdew")), 1)})
        return out
    beyond = _clist("beyond_pdew"); behind = _clist("behind_pdew")

    research = []
    order = ["corporate_links", "economic_context", "tourism", "trade", "airport_overview",
             "diaspora", "passenger_profile", "non_cannibalization", "case_study", "education"]
    for bid in order:
        blk = research_blocks.get(bid)
        if not blk or not blk.get("findings"):
            continue
        research.append({"title": BLOCK_TITLES.get(bid, bid.replace("_", " ").title()),
                         "findings": [{"claim": f.get("claim", ""), "source": f.get("source_name", ""),
                                       "year": f.get("year", "")} for f in blk["findings"]]})

    data = {
        "origin": {"iata": o.get("iata"), "city": o.get("city"), "country": o.get("country")},
        "dest": {"iata": d.get("iata"), "city": d.get("city"), "country": d.get("country")},
        "airline": airline, "date": inputs.get("date", ""),
        "demand": {"natural": round(_n(dem.get("natural"))), "captured": round(_n(dem.get("captured"))),
                   "feed_behind": round(_n(dem.get("feed_behind"))), "feed_beyond": round(_n(dem.get("feed_beyond"))),
                   "feed_behind_base": round(_n(dem.get("feed_behind_base"))),
                   "feed_beyond_base": round(_n(dem.get("feed_beyond_base"))),
                   "feed_total": round(_n(dem.get("feed_total"))), "total": round(_n(dem.get("total"))),
                   "stimulation": _n(dem.get("stimulation")) or 1.0, "qsi_share": _n(dem.get("qsi_share"))},
        "capacity": {"aircraft": cap.get("aircraft"), "freq": cap.get("freq"), "load": _n(cap.get("load")),
                     "carried": round(_n(cap.get("carried"))), "seats": ec.get("seats")},
        "cost_model": cm, "beyond": beyond, "behind": behind, "schedule": fc.get("schedule") or {},
        "research": research, "images": images,
    }
    return _HTML.replace("/*__DATA__*/", json.dumps(data))


# --------------------------------------------------------------------------------------------------
_HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Avia Cortex - Route Pitch</title>
<style>
:root{--navy:#0E1B33;--navy2:#1F3864;--accent:#2F6BF0;--accent2:#5C8DF6;--green:#0E9F6E;--amber:#C9781A;
--red:#D84C4C;--ink:#0F1C30;--body:#46566E;--muted:#8A97AB;--line:#E6EBF2;--bg:#F4F7FB;--card:#fff;
--font:-apple-system,"Segoe UI",Roboto,system-ui,Helvetica,Arial,sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font);background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased;line-height:1.5}
.wrap{max-width:940px;margin:0 auto;padding:0 0 60px}
.hero{position:relative;background:linear-gradient(135deg,var(--navy),var(--navy2));color:#fff;padding:46px 40px 40px;overflow:hidden}
.hero .bg{position:absolute;inset:0;background-size:cover;background-position:center;opacity:.28}
.hero .bg:after{content:"";position:absolute;inset:0;background:linear-gradient(135deg,rgba(14,27,51,.82),rgba(31,56,100,.72))}
.hero .in{position:relative;z-index:2}
.brand{display:flex;align-items:center;gap:10px;font-weight:700;letter-spacing:.4px;opacity:.9;font-size:13px;margin-bottom:26px}
.brand .m{width:26px;height:26px;border-radius:7px;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center}
.brand small{font-weight:500;letter-spacing:2px;color:#9fb2d6;font-size:10px}
.hero h1{font-size:40px;font-weight:800;letter-spacing:-.5px;line-height:1.05}
.hero .sub{font-size:16px;color:#c8d6ef;margin-top:8px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:30px}
.kpi{background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.14);border-radius:14px;padding:15px 16px;backdrop-filter:blur(4px)}
.kpi .l{font-size:10.5px;text-transform:uppercase;letter-spacing:.6px;color:#9fb2d6;font-weight:600}
.kpi .v{font-size:27px;font-weight:800;margin-top:5px;letter-spacing:-.5px}
.kpi .s{font-size:11.5px;color:#c8d6ef;margin-top:2px}
.sec{background:var(--card);margin:16px 20px 0;border:1px solid var(--line);border-radius:16px;padding:26px 28px;box-shadow:0 1px 2px rgba(16,32,60,.04),0 8px 24px rgba(16,32,60,.05)}
.sec h2{font-size:12px;text-transform:uppercase;letter-spacing:1.2px;color:var(--accent);font-weight:700;margin-bottom:14px}
.lead{font-size:16px;color:var(--ink);line-height:1.6}
.bars{margin-top:6px}
.bar{display:flex;align-items:center;gap:12px;margin:11px 0}
.bar .nm{width:170px;font-size:13px;color:var(--body);flex:0 0 auto;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-align:right}
.bar .tr{flex:1;background:var(--bg);border-radius:7px;height:26px;overflow:hidden;position:relative}
.bar .fl{height:100%;border-radius:7px;background:linear-gradient(90deg,var(--navy2),var(--accent));display:flex;align-items:center;justify-content:flex-end;padding-right:9px;color:#fff;font-size:12px;font-weight:700;min-width:38px}
.bar .fl.g{background:linear-gradient(90deg,var(--green),#38c58e)}
.rgrid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.rcard{border:1px solid var(--line);border-radius:13px;padding:16px 17px;background:#fbfcfe}
.rcard .t{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--accent);font-weight:700;margin-bottom:9px}
.rcard .f{font-size:13.5px;color:var(--ink);line-height:1.5;padding:8px 0;border-top:1px solid var(--line)}
.rcard .f:first-of-type{border-top:none}
.rcard .src{display:block;font-size:11px;color:var(--muted);margin-top:3px}
.econ{display:grid;grid-template-columns:1fr 1.05fr;gap:22px;align-items:start}
.ctl{margin:13px 0}
.ctl label{display:flex;justify-content:space-between;font-size:12px;color:var(--body);font-weight:600;margin-bottom:6px}
.ctl label b{color:var(--accent);font-weight:800}
.ctl input[type=range]{width:100%;accent-color:var(--accent)}
.epanel{background:linear-gradient(135deg,var(--navy),var(--navy2));border-radius:15px;padding:22px;color:#fff}
.epanel .big{font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:#9fb2d6;font-weight:600}
.epanel .prof{font-size:36px;font-weight:800;letter-spacing:-.5px;margin:4px 0 2px}
.epanel .ps{font-size:12.5px;color:#c8d6ef}
.emini{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:16px}
.emini div{background:rgba(255,255,255,.08);border-radius:11px;padding:11px 13px}
.emini .l{font-size:10px;text-transform:uppercase;letter-spacing:.5px;color:#9fb2d6;font-weight:600}
.emini .v{font-size:19px;font-weight:800;margin-top:2px}
.pl{margin-top:16px}
.pl .r{display:flex;justify-content:space-between;font-size:12.5px;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.09);color:#dbe6f7}
.pl .r b{color:#fff}
.note{font-size:12px;color:var(--muted);margin-top:14px;line-height:1.5}
.foot{margin:26px 20px 0;padding:20px 28px;color:var(--muted);font-size:12px;text-align:center}
.foot b{color:var(--body)}
.imgrow{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:6px}
.imgrow figure{border-radius:13px;overflow:hidden;border:1px solid var(--line);background:#eef2f8}
.imgrow img{width:100%;height:150px;object-fit:cover;display:block}
.imgrow figcaption{font-size:11.5px;color:var(--muted);padding:8px 12px}
.scroll{overflow-x:auto}
table.tbl{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:4px;min-width:520px}
.tbl th{background:var(--navy2);color:#fff;font-weight:700;text-align:right;padding:8px 9px;font-size:10.5px;text-transform:uppercase;letter-spacing:.3px}
.tbl th:first-child,.tbl th:nth-child(3){text-align:left}
.tbl td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:right;color:var(--body)}
.tbl td.b{font-weight:700;color:var(--ink)}
.tbl tr.tot td{font-weight:800;color:var(--ink);border-top:2px solid var(--navy);background:#f5f8fd}
.subh{font-size:13px;font-weight:700;color:var(--navy);margin:18px 0 4px}
@media(max-width:720px){.kpis{grid-template-columns:1fr 1fr}.econ{grid-template-columns:1fr}.rgrid{grid-template-columns:1fr}.hero h1{font-size:30px}.imgrow{grid-template-columns:1fr}}
</style></head>
<body><div class="wrap">
  <div class="hero"><div class="bg" id="heroImg"></div><div class="in">
    <div class="brand"><span class="m"><svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M3 12c4 0 5-7 9-7s5 14 9 7" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/></svg></span>
      AVIA&nbsp;CORTEX<small>ROUTE INTELLIGENCE</small></div>
    <h1 id="hTitle"></h1><div class="sub" id="hSub"></div>
    <div class="kpis" id="kpis"></div>
  </div></div>

  <div class="sec"><h2>The opportunity</h2><p class="lead" id="lead"></p></div>

  <div class="sec"><h2>Forecast, each way per year</h2><div class="bars" id="fcBars"></div></div>

  <div class="sec"><h2>Traffic forecast</h2><div class="scroll"><table class="tbl" id="fcTable"></table></div></div>

  <div class="sec" id="imgSec" style="display:none"><h2>The market</h2><div class="imgrow" id="imgRow"></div></div>

  <div class="sec"><h2>Connecting markets</h2><div class="bars" id="cxBars"></div>
    <div class="subh" id="cxBehindH"></div><div class="scroll"><table class="tbl" id="cxBehind"></table></div>
    <div class="subh" id="cxBeyondH"></div><div class="scroll"><table class="tbl" id="cxBeyond"></table></div></div>

  <div class="sec"><h2>Schedule and capacity</h2><div class="scroll"><table class="tbl" id="schedTable"></table></div>
    <div class="note">Departure and arrival are indicative local times from block time and timezone; not curfew- or slot-optimised.</div></div>

  <div class="sec"><h2>Route economics, move a slider</h2>
    <div class="econ"><div id="sliders"></div>
      <div class="epanel">
        <div class="big">Annual operating profit</div><div class="prof" id="eProf">-</div><div class="ps" id="ePs"></div>
        <div class="emini">
          <div><div class="l">Margin</div><div class="v" id="eMarg">-</div></div>
          <div><div class="l">Breakeven load</div><div class="v" id="eBe">-</div></div>
          <div><div class="l">Profit / rotation</div><div class="v" id="eRot">-</div></div>
          <div><div class="l">Pax / rotation</div><div class="v" id="ePax">-</div></div>
        </div>
        <div class="pl" id="ePl"></div>
      </div></div>
    <div class="note">Indicative, directional guidance. Central estimate on validated type costs; not the airline's actual costs. Adjust the sliders to test fares, fuel, frequency and cabin mix.</div>
  </div>

  <div class="sec" id="resSec"><h2>Why this route</h2><div class="rgrid" id="research"></div>
    <div class="note">Research auto-compiled from cited public sources and verified against the source page where possible; confirm figures before use.</div></div>

  <div class="foot" id="foot"></div>
</div>
<script>
const D=/*__DATA__*/;
const $=s=>document.querySelector(s);
const money=n=>{const v=Math.round(n||0);return (v<0?'-$':'$')+Math.abs(v).toLocaleString('en-GB');};
const fmt=n=>Math.round(n||0).toLocaleString('en-GB');
const fmtM=n=>n>=1e6?(n/1e6).toFixed(1)+'m':n>=1e3?Math.round(n/1e3)+'k':String(Math.round(n));

// hero + titles
$('#hTitle').textContent=`${D.origin.city} to ${D.dest.city}`;
$('#hSub').textContent=`A route opportunity for ${D.airline}  ·  ${D.capacity.aircraft||''} · ${D.capacity.freq||''}x weekly`+(D.date?`  ·  ${D.date}`:'');
if(D.images&&D.images.hero) $('#heroImg').style.backgroundImage=`url(${D.images.hero})`;
$('#kpis').innerHTML=[
  ['Total forecast',fmt(D.demand.total),'each way / year'],
  ['Load factor',Math.round(D.capacity.load*100)+'%','at '+(D.capacity.freq||'')+'x weekly'],
  ['Catchment capture',Math.round(D.demand.qsi_share*100)+'%','of the local market'],
  ['Connecting feed',fmt(D.demand.feed_total),'behind + beyond'],
].map(k=>`<div class="kpi"><div class="l">${k[0]}</div><div class="v">${k[1]}</div><div class="s">${k[2]}</div></div>`).join('');

$('#lead').textContent=`Cortex forecasts ${fmt(D.demand.total)} passengers each way per year on a nonstop ${D.origin.city} to ${D.dest.city} service. Demand is measured from Sabre Global Demand Data origin-and-destination traffic in the ${D.origin.city} catchment, where the new nonstop captures ${Math.round(D.demand.qsi_share*100)}% of a ${fmt(D.demand.natural)} addressable market, with ${D.airline}'s connecting feed added behind ${D.origin.city} and beyond ${D.dest.city}.`;

// forecast bars
(function(){
  const rows=[['Point to point',D.demand.captured,false],['Connecting behind '+D.origin.iata,D.demand.feed_behind,false],
    ['Connecting beyond '+D.dest.iata,D.demand.feed_beyond,false],['Total each way',D.demand.total,true]];
  const mx=Math.max(...rows.map(r=>r[1]))||1;
  $('#fcBars').innerHTML=rows.map(r=>`<div class="bar"><div class="nm">${r[0]}</div><div class="tr">
    <div class="fl ${r[2]?'g':''}" style="width:${Math.max(r[1]/mx*100,7)}%">${fmt(r[1])}</div></div></div>`).join('');
})();

// connecting markets chart
(function(){
  if(!D.beyond.length){ $('#cxBars').innerHTML='<div class="note">No connecting feed for this airline, or a point-to-point carrier.</div>'; return; }
  const mx=Math.max(...D.beyond.map(b=>b.pax))||1;
  $('#cxBars').innerHTML=D.beyond.map(b=>`<div class="bar"><div class="nm">${b.city}</div><div class="tr">
    <div class="fl" style="width:${Math.max(b.pax/mx*100,7)}%">${fmt(b.pax)}</div></div></div>`).join('');
})();

// full traffic forecast table
(function(){
  const dm=D.demand, freq=D.capacity.freq||7;
  const k=x=>(x/1000).toFixed(1), pt=x=>Math.round(x/(freq*52)), stim=dm.stimulation||1;
  const rows=[
    ['Point to point', dm.natural, dm.natural, stim, dm.natural*stim, dm.qsi_share, dm.captured],
    ['Connecting behind '+D.origin.iata, dm.feed_behind_base, dm.feed_behind_base, 1, dm.feed_behind_base, (dm.feed_behind_base?dm.feed_behind/dm.feed_behind_base:0), dm.feed_behind],
    ['Connecting beyond '+D.dest.iata, dm.feed_beyond_base, dm.feed_beyond_base, 1, dm.feed_beyond_base, (dm.feed_beyond_base?dm.feed_beyond/dm.feed_beyond_base:0), dm.feed_beyond]];
  let h='<tr><th>Market</th><th>Base (000s)</th><th>Growth</th><th>Grown (000s)</th><th>Stim.</th><th>Stimulated (000s)</th><th>Capture</th><th>Forecast (000s)</th><th>PTEW</th></tr>';
  rows.forEach(r=>{ h+=`<tr><td class="b">${r[0]}</td><td>${r[1]?k(r[1]):'-'}</td><td>0%</td><td>${r[2]?k(r[2]):'-'}</td><td>${r[3].toFixed(2)}</td><td>${r[4]?k(r[4]):'-'}</td><td>${r[5]?(r[5]*100).toFixed(1)+'%':'-'}</td><td class="b">${k(r[6])}</td><td>${pt(r[6])}</td></tr>`; });
  h+=`<tr class="tot"><td>Grand total</td><td>-</td><td></td><td>-</td><td></td><td>-</td><td></td><td>${k(dm.total)}</td><td>${pt(dm.total)}</td></tr>`;
  $('#fcTable').innerHTML=h;
})();

// connecting-city tables (base demand, share, forecast, PDEW)
function cxtbl(list,elid,hid,label){
  const el=$('#'+elid), hh=$('#'+hid);
  if(!list||!list.length){ if(hh)hh.style.display='none'; if(el)el.style.display='none'; return; }
  hh.textContent=label;
  let h='<tr><th>Nr</th><th>Code</th><th>City</th><th>Country</th><th>Annual demand</th><th>Share</th><th>Annual forecast</th><th>PDEW</th></tr>',tb=0,tf=0;
  list.forEach((r,i)=>{ tb+=r.base; tf+=r.pax;
    h+=`<tr><td>${i+1}</td><td>${r.code||''}</td><td class="b" style="text-align:left">${r.city}</td><td style="text-align:left">${r.country||''}</td><td>${r.base?fmt(r.base):'-'}</td><td>${r.base?(r.share*100).toFixed(1)+'%':'-'}</td><td>${fmt(r.pax)}</td><td>${r.pdew.toFixed(1)}</td></tr>`; });
  h+=`<tr class="tot"><td></td><td></td><td>Total</td><td></td><td>${tb?fmt(tb):'-'}</td><td></td><td>${fmt(tf)}</td><td></td></tr>`;
  el.innerHTML=h;
}
cxtbl(D.behind,'cxBehind','cxBehindH','Connecting at '+D.origin.iata+' (behind the origin)');
cxtbl(D.beyond,'cxBeyond','cxBeyondH','Connecting at '+D.dest.iata+' (beyond the destination)');

// schedule and capacity
(function(){
  const c=D.capacity, seats=c.seats||0, freq=c.freq||0, annS=seats*freq*52, sc=D.schedule||{};
  let h='<tr><th>Sector</th><th>Dep</th><th>Arr</th><th>Op days/wk</th><th>Aircraft</th><th>Seats</th><th>Annual seats</th><th>Annual pax</th><th>Seat factor</th></tr>';
  ['outbound','inbound'].forEach(leg=>{ const s=sc[leg]||{};
    const sector=s.sector||(leg==='outbound'?D.origin.iata+'-'+D.dest.iata:D.dest.iata+'-'+D.origin.iata);
    h+=`<tr><td class="b" style="text-align:left">${sector}</td><td>${s.dep||'-'}</td><td>${s.arr||'-'}</td><td>${freq}</td><td>${c.aircraft||''}</td><td>${fmt(seats)}</td><td>${fmt(annS)}</td><td>${fmt(D.demand.total)}</td><td>${Math.round(c.load*100)}%</td></tr>`; });
  h+=`<tr class="tot"><td>Total</td><td></td><td></td><td></td><td></td><td></td><td>${fmt(annS*2)}</td><td>${fmt(D.demand.total*2)}</td><td>${Math.round(c.load*100)}%</td></tr>`;
  $('#schedTable').innerHTML=h;
})();

// images
if(D.images&&(D.images.origin||D.images.dest)){
  $('#imgSec').style.display='';
  const cells=[];
  if(D.images.dest) cells.push(`<figure><img src="${D.images.dest}" alt=""><figcaption>${D.dest.city}, ${D.dest.country||''}</figcaption></figure>`);
  if(D.images.origin) cells.push(`<figure><img src="${D.images.origin}" alt=""><figcaption>${D.origin.city}, ${D.origin.country||''}</figcaption></figure>`);
  $('#imgRow').innerHTML=cells.join('');
}

// research cards
(function(){
  if(!D.research.length){ $('#resSec').style.display='none'; return; }
  $('#research').innerHTML=D.research.map(b=>`<div class="rcard"><div class="t">${b.title}</div>`+
    b.findings.map(f=>`<div class="f">${f.claim}<span class="src">${f.source}${f.year?' · '+f.year:''}</span></div>`).join('')+`</div>`).join('');
})();

// ---- live economics ----
const CM=D.cost_model||{};
function econLFs(dem,ps,freq,plf){const e=CM.econ_seats*freq*52,b=CM.bus_seats*freq*52;
  return [e?Math.min(dem*(1-ps)/e,plf):0, b?Math.min(dem*ps/b,plf):0];}
function turn(le,lb,ef,bf,fp){
  const pax=2*(CM.econ_seats*le+CM.bus_seats*lb);
  const erev=2*CM.econ_seats*le*ef, brev=2*CM.bus_seats*lb*bf, net=erev+brev;
  const gross=net+(CM.cargo_rev||0)+(CM.recovery_per_pax||0)*pax;
  const fuel=(CM.fuel_kg_per_turn||0)*fp, perpax=(CM.per_pax_cost||0)*pax, fixed=(CM.fixed_per_turn||0), indirect=(CM.indirect_rate||0)*net;
  const cost=fuel+perpax+fixed+indirect, profit=gross-cost;
  const seatRev=gross/((CM.econ_seats+CM.bus_seats)*2||1), be=seatRev?cost/(gross)* (dem=>1)(0)+0:0;
  const belf=gross>0?Math.min(cost/gross,1.5):0;
  return {pax,gross,fuel,perpax,fixed,indirect,cost,profit,margin:gross?profit/gross:0,net,belf};
}
const SL=[['freq','Frequency (each way / week)',3,21,1,CM.freq||7,v=>v],
  ['plf','Planning load-factor cap',0.6,0.92,0.01,CM.plan_lf||0.875,v=>Math.round(v*100)+'%'],
  ['ef','Economy fare (one-way)',120,1200,10,CM.econ_fare||300,v=>'$'+v],
  ['bf','Business fare (one-way)',600,5000,50,CM.bus_fare||1400,v=>'$'+(+v).toLocaleString()],
  ['fp','Jet fuel ($/kg)',0.55,1.4,0.01,CM.ref_fuel_price||0.9,v=>'$'+(+v).toFixed(2)],
  ['ps','Premium share of demand',0,0.3,0.01,CM.bus_seats>0?0.12:0,v=>Math.round(v*100)+'%']];
$('#sliders').innerHTML=SL.map(s=>`<div class="ctl"><label>${s[1]} <b id="o_${s[0]}"></b></label>
  <input id="s_${s[0]}" type="range" min="${s[2]}" max="${s[3]}" step="${s[4]}" value="${s[5]}"></div>`).join('');
if(CM.bus_seats<=0){const b=$('#s_bf'); if(b) b.closest('.ctl').style.opacity=.4;}
function recompute(){
  const g=id=>+$('#s_'+id).value;
  SL.forEach(s=>$('#o_'+s[0]).textContent=s[6](g(s[0])));
  const freq=g('freq'),plf=g('plf'),ef=g('ef'),bf=g('bf'),fp=g('fp'),ps=g('ps');
  const dem=(CM.each_way||D.demand.total||0);
  const [le,lb]=econLFs(dem,ps,freq,plf), t=turn(le,lb,ef,bf,fp);
  const annual=t.profit*freq*52, carried=Math.round(2*(CM.econ_seats*le+CM.bus_seats*lb)*freq*52);
  $('#eProf').textContent=money(annual); $('#eProf').style.color=annual>=0?'#fff':'#F5B4B4';
  $('#ePs').textContent=`margin ${(t.margin*100).toFixed(1)}% · ${carried.toLocaleString()} pax/yr · ${freq}x weekly`;
  $('#eMarg').textContent=(t.margin*100).toFixed(1)+'%';
  $('#eBe').textContent=Math.round(t.belf*100)+'%';
  $('#eRot').textContent=money(t.profit);
  $('#ePax').textContent=fmt(t.pax);
  $('#ePl').innerHTML=[['Revenue',t.gross],['Fuel',-t.fuel],['Fixed (maint, own, crew, charges)',-t.fixed],
    ['Per-passenger',-t.perpax],['Overhead and sales',-t.indirect]]
    .map(r=>`<div class="r"><span>${r[0]}</span><span>${money(r[1])}</span></div>`).join('')
    +`<div class="r"><b>Operating profit / rotation</b><b>${money(t.profit)}</b></div>`;
}
SL.forEach(s=>$('#s_'+s[0]).addEventListener('input',recompute));
recompute();

$('#foot').innerHTML=`<b>Avia Solutions Limited</b> · Prepared for ${D.airline}${D.date?' · '+D.date:''}<br>Powered by Avia Cortex. Indicative central estimate for directional guidance.`;
</script></body></html>"""
