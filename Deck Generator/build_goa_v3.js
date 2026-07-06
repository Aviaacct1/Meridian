// Avia Solutions - BA LHR-SJC deck, built to the precise house template (spec v1).
// House style: UK English, no em/en dashes, "circa". Author Avia Solutions.
const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Avia Solutions";
pres.company = "Avia Solutions";
pres.title = "A Transatlantic Opportunity: New York from Genoa";

// ---- House palette (dark blue / cyan / orange) ----
const DARK="1F3864", DARK2="2E5496", CYAN="00B0F0", ORANGE="ED7D31", GREEN="70AD47";
const INK="3A3A3A", MUT="7F7F7F", WHITE="FFFFFF", LIGHT="F2F5F9", PANEL="E3E9F2", LINE="D4DCE6";
const T="Arial", B="Arial";
const W=13.333, Hh=7.5, MX=0.7;
const MAP="route_map.png";
let pg=0;
const EVENT="World Routes 2026";

function header(s){
  s.addText("A Transatlantic Opportunity: New York from Genoa",{x:MX,y:0.16,w:8.5,h:0.25,fontSize:8.5,fontFace:B,color:MUT,margin:0,valign:"middle"});
  s.addText(EVENT,{x:W-3.8,y:0.16,w:3.1,h:0.25,fontSize:8.5,fontFace:B,color:MUT,align:"right",margin:0,valign:"middle"});
  s.addShape(pres.shapes.LINE,{x:MX,y:0.44,w:W-2*MX,h:0,line:{color:LINE,width:0.75}});
}
function footer(s){
  pg++;
  s.addText("AviaSolutions analysis",{x:MX,y:Hh-0.36,w:5,h:0.26,fontSize:8,fontFace:B,color:MUT,italic:true,margin:0,valign:"middle"});
  s.addText("[ Airline logo ]",{x:W-3.4,y:Hh-0.36,w:2.2,h:0.26,fontSize:8,fontFace:B,color:MUT,align:"right",margin:0,valign:"middle"});
  s.addText(String(pg),{x:W-1.0,y:Hh-0.36,w:0.5,h:0.26,fontSize:9,fontFace:B,color:MUT,align:"right",margin:0,valign:"middle"});
}
function title(s,t,sub){
  s.addText(t,{x:MX,y:0.62,w:W-2*MX,h:0.55,fontSize:24,fontFace:T,color:DARK,bold:true,margin:0,valign:"middle"});
  if(sub) s.addText(sub,{x:MX,y:1.18,w:W-2*MX,h:0.34,fontSize:13,fontFace:B,color:CYAN,bold:true,margin:0,valign:"middle"});
}
function src(s,t){ s.addText("Source: "+t,{x:MX,y:Hh-0.62,w:W-2*MX,h:0.24,fontSize:7.5,fontFace:B,color:MUT,italic:true,margin:0,valign:"middle"}); }
function sh(){ return {type:"outer",color:"000000",blur:6,offset:2,angle:90,opacity:0.12}; }
function stat(s,x,y,w,h,v,l,sub,acc){
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x,y,w,h,fill:{color:WHITE},line:{color:PANEL,width:1},rectRadius:0.05,shadow:sh()});
  s.addText(v,{x:x+0.16,y:y+0.14,w:w-0.32,h:h*0.46,fontSize:26,fontFace:T,color:acc||DARK,bold:true,margin:0,valign:"middle",autoFit:true});
  s.addText(l,{x:x+0.18,y:y+h*0.52,w:w-0.36,h:h*0.24,fontSize:11,fontFace:B,color:INK,bold:true,margin:0,valign:"top"});
  if(sub) s.addText(sub,{x:x+0.18,y:y+h*0.73,w:w-0.36,h:h*0.25,fontSize:9,fontFace:B,color:MUT,margin:0,valign:"top"});
}
function bullets(s,x,y,w,h,items,fs){
  s.addText(items.map(t=>({text:t,options:{bullet:{code:"2022",indent:13},color:INK,breakLine:true,paraSpaceAfter:7}})),{x,y,w,h,fontSize:fs||12.5,fontFace:B,valign:"top",margin:0});
}
function pslot(s,x,y,w,h,label){
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x,y,w,h,fill:{color:PANEL},line:{color:MUT,width:1,dashType:"dash"},rectRadius:0.04});
  s.addText([{text:"IMAGE SLOT",options:{bold:true,color:DARK2,fontSize:10,breakLine:true,charSpacing:1}},{text:label,options:{color:MUT,fontSize:9,breakLine:true}},{text:"airport / library image",options:{color:MUT,fontSize:8,italic:true}}],{x:x+0.1,y,w:w-0.2,h,align:"center",valign:"middle",fontFace:B,margin:0});
}
function divider(num,name,photo){
  const s=pres.addSlide(); s.background={color:DARK};
  pslot2(s,0,0,W,Hh); // full-bleed image slot behind
  s.addShape(pres.shapes.RECTANGLE,{x:0,y:3.0,w:W,h:1.7,fill:{color:DARK,transparency:18}});
  s.addText(num,{x:MX,y:2.55,w:3,h:0.7,fontSize:20,fontFace:T,color:ORANGE,bold:true,margin:0});
  s.addText(name,{x:MX,y:3.15,w:11,h:1.3,fontSize:34,fontFace:T,color:WHITE,bold:true,margin:0,valign:"top"});
  pg++;
}
function pslot2(s,x,y,w,h){ // full-bleed divider image placeholder
  s.addShape(pres.shapes.RECTANGLE,{x,y,w,h,fill:{color:DARK2},line:{type:"none"}});
  s.addText("FULL-BLEED IMAGE SLOT  (San Jose / Silicon Valley)",{x:0,y:0.3,w:W,h:0.3,fontSize:9,fontFace:B,color:"AEBED4",align:"center",italic:true,margin:0});
}
function tbl(s,x,y,w,rows,colW,fs,rowH){
  s.addTable(rows,{x,y,w,colW,fontFace:B,fontSize:fs||10,border:{type:"solid",pt:0.5,color:LINE},valign:"middle",rowH:rowH||0.34});
}
function hcell(t,al){ return {text:t,options:{bold:true,color:WHITE,fill:{color:DARK},align:al||"left",fontSize:9}}; }
function cell(t,al,i,bold,col){ return {text:t,options:{fill:{color:i%2?LIGHT:WHITE},color:col||INK,align:al||"left",bold:!!bold,fontSize:9}}; }

// ============= 1 TITLE
{ const s=pres.addSlide(); s.background={color:DARK};
  s.addShape(pres.shapes.RECTANGLE,{x:0,y:0,w:W,h:3.0,fill:{color:DARK2}});
  s.addText("FULL-BLEED IMAGE SLOT  (Genoa / Italian Riviera hero)",{x:0,y:1.35,w:W,h:0.3,fontSize:10,fontFace:B,color:"AEBED4",align:"center",italic:true,margin:0});
  s.addText("A Transatlantic Opportunity:\nNew York from Genoa",{x:MX,y:3.35,w:11.8,h:1.5,fontSize:38,fontFace:T,color:WHITE,bold:true,margin:0,lineSpacingMultiple:1.02});
  s.addText("Aeroporto di Genova Cristoforo Colombo  |  Genoa - New York  |  Airbus A321XLR",{x:MX,y:5.05,w:11.8,h:0.4,fontSize:15,fontFace:B,color:CYAN,bold:true,margin:0});
  s.addText(EVENT,{x:MX,y:5.6,w:8,h:0.35,fontSize:13,fontFace:B,color:"C9D6E8",margin:0});
  s.addText("Prepared by Avia Solutions  |  June 2026",{x:MX,y:6.0,w:8,h:0.3,fontSize:11,fontFace:B,color:MUT,margin:0});
  s.addText("[ Airport logo ]      [ Avia Solutions logo ]      [ Airline logo ]",{x:MX,y:6.7,w:11,h:0.35,fontSize:10,fontFace:B,color:MUT,italic:true,margin:0});
}
// ============= 2 CONTENTS
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s); title(s,"Contents");
  const items=[["1","Summary of Route Forecast","4"],["2","Why New York from Genoa","5"],["3","The Case and the Precedent","9"],["4","Genoa - New York Forecast","13"],["5","Revenue and Economics","17"],["6","Genoa Airport","19"],["7","Appendix: Methodology","21"]];
  let y=1.85; items.forEach(([n,t,p])=>{ s.addText(n,{x:MX,y,w:0.6,h:0.5,fontSize:18,fontFace:T,color:ORANGE,bold:true,margin:0,valign:"top"}); s.addText(t,{x:MX+0.75,y,w:10.2,h:0.5,fontSize:15,fontFace:B,color:DARK,bold:true,margin:0,valign:"top"}); s.addText(p,{x:W-1.4,y,w:0.7,h:0.5,fontSize:13,fontFace:B,color:MUT,align:"right",margin:0,valign:"top"}); y+=0.66; });
  footer(s);
}
// ============= 3 OVERVIEW
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Genoa is well placed to anchor a New York service for Liguria");
  bullets(s,MX,1.65,6.05,5.0,[
    "New York holds the largest Italian-American population on earth: circa 2.6m in the metro, circa 6.3m across the US northeast.",
    "Liguria set a tourism record in 2024 at 16.2m arrivals, led by foreign demand, with the Cinque Terre and Portofino within an hour of the airport.",
    "The US is Italy's premium inbound market: circa 4.1m travellers spending over EUR 6.6bn in 2025, the highest per-night spend of any nationality.",
    "Genoa is a major cruise homeport: circa 620,000 air-relevant embarkation passengers a year.",
  ],11.5);
  bullets(s,MX+6.35,1.65,5.55,5.0,[
    "The catchment generates circa 553,300 New York passengers a year, almost all leaking out through Milan today.",
    "The A321XLR makes a thin transatlantic market viable, and United is already opening Newark nonstops to secondary Italian cities.",
    "A daily aircraft fills in peak season; a seasonal, building pattern is the prudent launch.",
    "Honest read: a mainly point-to-point leisure and VFR market, thinner than a hub route, with a modest business layer.",
  ],11.5);
  src(s,"AviaSolutions analysis; US Census ACS 2024; Regione Liguria; Bank of Italy; Ports of Genoa (2024-2026)"); footer(s);
}
// ============= 4 SUMMARY OF ROUTE FORECAST (MAP)
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Opportunity at Genoa: Summary of Route Forecast");
  const figs=[["New York O&D market","553,300",DARK],["Recaptured by a Genoa nonstop","62,600",DARK2],["Connecting market","Limited",CYAN]];
  figs.forEach(([l,v,c],i)=>{ const y=1.7+i*1.15; s.addText(v,{x:MX,y,w:3.3,h:0.6,fontSize:30,fontFace:T,color:c,bold:true,margin:0,valign:"middle"}); s.addText(l,{x:MX,y:y+0.62,w:3.3,h:0.5,fontSize:11,fontFace:B,color:INK,margin:0,valign:"top"}); });
  s.addText("* Each way, based on AviaSolutions' Genoa catchment analysis.",{x:MX,y:5.3,w:4,h:0.5,fontSize:8,fontFace:B,color:MUT,italic:true,margin:0});
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:4.3,y:1.62,w:8.3,h:3.55,fill:{color:LIGHT},line:{color:PANEL,width:1},rectRadius:0.04});
  s.addImage({path:MAP,x:4.4,y:1.7,w:8.1,h:3.4,sizing:{type:"cover",w:8.1,h:3.4}});
  s.addText("Schedule Options: Airbus A321XLR",{x:MX,y:5.55,w:6,h:0.3,fontSize:12,fontFace:T,color:DARK,bold:true,margin:0});
  const sr=[["Sector","Dep.","Arr.","Op. Days","Aircraft","Seats","Annual Seats","Annual Pax","Seat Factor"].map(h=>hcell(h,h==="Sector"?"left":"center")),
    ["GOA-JFK","10:30","14:00","Seasonal","A321XLR","182","66,248","62,600",""].map((c,j)=>cell(c,j===0?"left":"center",0)),
    ["JFK-GOA","19:00","08:30","Seasonal","A321XLR","182","66,248","62,600",""].map((c,j)=>cell(c,j===0?"left":"center",1)),
    ["Total","","","Building","A321XLR","","132,496","125,200","circa 90%"].map((c,j)=>cell(c,j===0?"left":"center",0,true,DARK))];
  tbl(s,MX,5.88,11.9,sr,[1.3,0.85,0.85,1.2,1.1,0.95,1.6,1.5,1.55],9,0.32);
  footer(s);
}
// ============= SECTION 2 Why New York
divider("Section 2","Why New York from Genoa","Genoa old port");
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"The largest Italian-American market on earth","A deep, year-round visiting-friends base");
  stat(s,MX,1.7,3.4,2.0,"circa 2.6m","Italians in the New York metro","The largest of any US metro",DARK);
  s.addText("Italian-American population by US metro (millions)",{x:MX+3.75,y:1.62,w:7.85,h:0.3,fontSize:11,fontFace:T,color:DARK,bold:true,margin:0});
  s.addChart(pres.charts.BAR,[{name:"Pop",labels:["New York","Philadelphia","Boston","Chicago","Los Angeles"],values:[2.6,1.3,0.9,0.8,0.7]}],{x:MX+3.6,y:1.95,w:8.0,h:1.85,barDir:"bar",chartColors:[DARK2],showValue:true,dataLabelPosition:"outEnd",dataLabelColor:INK,dataLabelFontSize:9,dataLabelFontFace:B,catAxisLabelColor:MUT,catAxisLabelFontSize:9,valAxisHidden:true,valGridLine:{style:"none"},catGridLine:{style:"none"},showLegend:false,chartArea:{fill:{color:WHITE}}});
  bullets(s,MX,3.95,11.9,2.0,[
    "The New York region holds the densest Italian-American population anywhere outside Italy, circa 39% of the US total across the northeast.",
    "A resilient, year-round visiting-friends-and-relatives base, less seasonal and less price-sensitive than pure leisure.",
    "Genoa carries a direct hook: the city is the birthplace of Christopher Columbus, the figure at the centre of New York's Italian-American identity.",
  ],12);
  src(s,"US Census Bureau ACS 2024 (B04006); ENIT / ForwardKeys (2026)"); footer(s);
}
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"A record tourism region and a premium US market","High-spend, long-stay leisure demand");
  stat(s,MX,1.7,3.55,1.6,"16.2m","Liguria arrivals, 2024","An all-time record, foreign-led",DARK);
  stat(s,MX+3.75,1.7,3.55,1.6,"circa 4.1m","US travellers to Italy","Spending over EUR 6.6bn in 2025",DARK2);
  stat(s,MX+7.5,1.7,3.55,1.6,"EUR 191","US spend per night","The highest of any nationality",ORANGE);
  bullets(s,MX,3.45,11.9,2.4,[
    "The region packs world-class draws within an hour of the airport: the Cinque Terre, Portofino, the Riviera and a UNESCO-listed historic centre.",
    "Genoa was Lonely Planet's only Italian Best in Travel city for 2025, fresh visibility in the US market.",
    "US traffic to Southern Europe runs circa 27% above 2019; the profile is long-stay (8-10 nights) and 88% leisure.",
  ],12);
  src(s,"Regione Liguria Tourism Observatory (2025); ENIT / Bank of Italy (2026); Lonely Planet 2025"); footer(s);
}
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"A major cruise homeport","Air-relevant embarkation demand on top of leisure");
  bullets(s,MX,1.7,7.2,3.4,[
    "Genoa is the seventh-largest cruise port in the Mediterranean, circa 1.6m cruise passengers in 2025.",
    "Of these, circa 620,000 are homeport passengers who travel to or from Genoa, many by air.",
    "Genoa is the home of Costa Cruises and an MSC base; MSC already sells flight-inclusive packages with a Genoa airport lounge.",
    "The United States is the world's largest cruise source market, so a New York nonstop strengthens Genoa as a transatlantic embarkation port.",
  ],12);
  stat(s,MX+7.5,1.7,4.1,1.6,"circa 620,000","air-relevant cruise pax","Homeport passengers, 2025",DARK);
  pslot(s,MX+7.5,3.5,4.1,1.6,"Genoa cruise terminal / ship");
  src(s,"Risposte Turismo / Seatrade (2026); Ports of Genoa; MSC Cruises"); footer(s);
}
// ============= SECTION 3 Case and precedent
divider("Section 3","The Case and the Precedent","United A321XLR at Newark");
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"The A321XLR makes a thin route viable","The aircraft that opens secondary-city transatlantic markets");
  stat(s,MX,1.7,3.55,1.6,"4,700nm","A321XLR range","Genoa to New York is circa 3,750nm",DARK);
  stat(s,MX+3.75,1.7,3.55,1.6,"circa 182","seats","A fraction of a widebody's demand need",DARK2);
  stat(s,MX+7.5,1.7,3.55,1.6,"2025-26","transatlantic entry","Aer Lingus, Iberia, JetBlue, United",CYAN);
  bullets(s,MX,3.45,11.9,2.4,[
    "The A321XLR carries circa 180 to 200 passengers across the Atlantic, opening routes no widebody could fill daily.",
    "Genoa to New York is comfortably inside the type's range, and the runway and apron handle the aircraft without constraint.",
    "United took its first A321XLR at Newark in June 2026, the natural operator for this route.",
  ],12);
  src(s,"Airbus; AeroXplorer (United XLR, Jun 2026); The Points Guy"); footer(s);
}
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"The precedent: United's secondary-Italy nonstops","A proven template that Genoa fits precisely");
  const rows=[["City","Route","Status","Frequency"].map(h=>hcell(h,"left")),
    ...[["Naples","Newark, plus Chicago and Atlanta","Established, expanded 2024-2025","Up to twice daily"],["Palermo","Newark (United, only US carrier)","Launched May 2025","3 weekly, building"],["Bari","Newark (United, only US carrier)","Launches May 2026","4 weekly, Boeing 767"],["Genoa","New York (proposed)","The opportunity","Seasonal, building"]].map((r,i)=>r.map(c=>({text:c,options:{fill:{color:i===3?PANEL:(i%2?LIGHT:WHITE)},color:i===3?DARK:INK,bold:i===3,align:"left",fontSize:11}})))];
  tbl(s,MX,1.75,11.9,rows,[2.0,3.9,3.6,2.4],11,0.55);
  s.addText("United is systematically opening Newark nonstops from secondary European cities (Palermo, Bari, Glasgow, Bilbao) at 3 to 4 weekly. Genoa is a mid-sized Italian city with strong US leisure demand and no incumbent nonstop: the same case.",{x:MX,y:4.8,w:11.9,h:0.9,fontSize:12,fontFace:B,color:DARK2,italic:true,margin:0,valign:"top"});
  src(s,"Air Service One (May 2025); AFAR citing United (Oct 2025)"); footer(s);
}
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Seasonality: a summer-led, building pattern","Why a seasonal launch is the prudent base case");
  s.addChart(pres.charts.BAR,[{name:"Indicative load factor",labels:["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],values:[55,55,62,75,85,92,96,96,90,78,60,58]}],{x:MX,y:1.7,w:7.6,h:3.9,barDir:"col",chartColors:[DARK2],catAxisLabelColor:MUT,valAxisLabelColor:MUT,catAxisLabelFontSize:9,valGridLine:{color:PANEL,size:0.5},catGridLine:{style:"none"},showLegend:false,valAxisMaxVal:100,valAxisMinVal:0,chartArea:{fill:{color:WHITE}}});
  bullets(s,MX+7.9,1.9,3.7,3.6,["Mediterranean leisure demand is highly seasonal, peaking June to September.","The prudent launch mirrors United's secondary-Italy routes: seasonal, late April to October.","Year-round service would lean on the visiting-friends and business layers, which are real but thinner."],12);
  src(s,"AviaSolutions analysis; Eurostat seasonality (2025). Monthly profile illustrative."); footer(s);
}
// ============= SECTION 4 Forecast
divider("Section 4","Genoa - New York Forecast","Liguria catchment map");
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"The catchment and the leak to Milan","Genoa's New York demand drives two hours to Malpensa today");
  bullets(s,MX,1.7,7.2,3.4,[
    "The Genoa catchment generates circa 553,300 two-way passengers a year to New York, but almost none flies from Genoa.",
    "With no nonstop, Liguria passengers drive circa two hours to Milan Malpensa, or connect over Rome, Munich or Amsterdam.",
    "Milan Malpensa runs circa four daily New York nonstops; that is the pool a Genoa service would partly recapture.",
    "Recapturing local demand onto a local nonstop is the core of the case, the same logic that built United's secondary-Italy routes.",
  ],12);
  stat(s,MX+7.5,1.7,4.1,1.6,"circa 198 km","Genoa to Malpensa","A two-hour drive each way",DARK);
  stat(s,MX+7.5,3.5,4.1,1.6,"circa 4 daily","Milan - New York nonstops","The leakage a Genoa service recaptures",DARK2);
  src(s,"AviaSolutions QSI catchment model; OAG"); footer(s);
}
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Route Forecast: recapturing the leakage","What a daily A321XLR can carry");
  const hd=["Demand layer","Passengers (each way)","Note"].map((h,j)=>hcell(h,j===1?"right":"left"));
  const rows=[hd,
    ["Natural catchment demand to New York","circa 92,500","Genoa's own addressable market"].map((c,j)=>cell(c,j===1?"right":"left",0)),
    ["Captured at Genoa today","circa 7,000","Almost all leaks to Milan"].map((c,j)=>cell(c,j===1?"right":"left",1)),
    ["Leaked pool a nonstop can win","circa 85,500","Demand driving past Genoa"].map((c,j)=>cell(c,j===1?"right":"left",0)),
    ["Repatriated at 65% capture","circa 55,600","Bounded, conservative capture"].map((c,j)=>cell(c,j===1?"right":"left",1)),
    ["Genoa nonstop forecast","circa 62,600","Captured plus repatriated"].map((c,j)=>cell(c,j===1?"right":"left",0,true,DARK))];
  tbl(s,MX,1.8,11.9,rows,[4.6,3.0,4.3],11,0.52);
  s.addText("Note: Genoa is a point-to-point market. Unlike a hub route there is little connecting demand to tabulate beyond New York or beyond Genoa, so the forecast rests on catchment recapture and stimulation.",{x:MX,y:4.95,w:11.9,h:0.7,fontSize:11,fontFace:B,color:DARK2,italic:true,margin:0,valign:"top"});
  src(s,"AviaSolutions QSI catchment and repatriation model (Sabre O&D)"); footer(s);
}
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Forecast detail by cabin","Revenue quality on a leisure-led market");
  const hd=["Cabin","Demand (each way)","Share","One-way fare","Share of revenue"].map((h,j)=>hcell(h,j===0?"left":"right"));
  const rows=[hd,
    ["Economy","circa 50,100","80%","circa $345","circa 50%"].map((c,j)=>cell(c,j===0?"left":"right",0)),
    ["Business","circa 12,500","20%","circa $1,400","circa 50%"].map((c,j)=>cell(c,j===0?"left":"right",1)),
    ["Total each way","circa 62,600","100%","","100%"].map((c,j)=>cell(c,j===0?"left":"right",0,true,DARK))];
  tbl(s,MX,1.8,11.9,rows,[2.6,2.6,2.5,2.1,2.1],11,0.48);
  stat(s,MX,3.7,3.7,1.5,"circa 125,200","annual passengers","Both directions combined",DARK);
  stat(s,MX+3.95,3.7,3.7,1.5,"182 seats","Airbus A321XLR","20 business, 162 economy",DARK2);
  stat(s,MX+7.9,3.7,3.7,1.5,"circa 90%+","peak load factor","Demand fills the aircraft in season",ORANGE);
  s.addText("Business is one in five passengers but circa half of ticket revenue, the quality that supports a premium single-aisle cabin.",{x:MX,y:5.4,w:11.9,h:0.4,fontSize:11,fontFace:B,color:DARK2,italic:true,margin:0});
  src(s,"AviaSolutions revenue model; cabin split from the Genoa case. Illustrative."); footer(s);
}
// ============= SECTION 5 Economics
divider("Section 5","Revenue and Economics","A321XLR cabin");
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Market Forecast Scenario: Genoa - New York","The economic picture, with an honest read on the cost base");
  const m=[["Equipment","Airbus A321XLR"],["Weekly departures (peak)","7"],["Business cabin seats","20"],["Economy seats","162"],["Total seats","182"],["Total load factor (peak)","circa 90%"],["Average one-way economy fare","circa $345"],["Average one-way business fare","circa $1,400"],["Passenger revenue (annual)","circa $70m"],["Cargo and ancillary","circa $3m"],["Total revenue (annual)","circa $73m"],["Breakeven load factor","circa 62%"]];
  const half=Math.ceil(m.length/2);
  const L=[["Metric","Value"].map(h=>hcell(h,h==="Metric"?"left":"right"))]; m.slice(0,half).forEach((r,i)=>L.push(r.map((c,j)=>cell(c,j===0?"left":"right",i))));
  const R=[["Metric","Value"].map(h=>hcell(h,h==="Metric"?"left":"right"))]; m.slice(half).forEach((r,i)=>R.push(r.map((c,j)=>cell(c,j===0?"left":"right",i))));
  tbl(s,MX,1.7,5.75,L,[3.9,1.85],10.5,0.46); tbl(s,MX+6.15,1.7,5.75,R,[3.9,1.85],10.5,0.46);
  s.addText("Honest caveat: the cost base is extrapolated for a new-generation narrowbody with no startup ramp modelled. Pressure-test the cost side before any commitment.",{x:MX,y:5.5,w:11.9,h:0.5,fontSize:11,fontFace:B,color:ORANGE,italic:true,margin:0,valign:"top"});
  src(s,"AviaSolutions revenue and aircraft economics model. Illustrative, seasonal-adjusted annual basis."); footer(s);
}
// ============= SECTION 6 Airport
divider("Section 6","Genoa Airport","Genoa Cristoforo Colombo airfield");
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Genoa airport: the hard facts","From the AIP and airport data, held offline in the tool");
  const fields=[["ICAO / IATA","LIMJ / GOA"],["Coordinates","44.4133 N, 008.8375 E"],["Elevation","13 ft (4 m), sea level"],["Runway","10/28, 2,915 m x 45 m, asphalt"],["Approach","ILS, precision approach"],["Aircraft stands","32, of which 6 widebody-capable"],["2025 passengers","1.58m, a record (+18%)"],["Distance to city","circa 6 km to Genoa centre"]];
  const rows=fields.map((r,i)=>r.map((c,j)=>cell(c,"left",i,j===0,j===0?DARK:INK)));
  tbl(s,MX,1.7,7.2,rows,[2.6,4.6],11,0.45);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX+7.5,y:1.7,w:4.1,h:2.1,fill:{color:LIGHT},line:{color:ORANGE,width:1},rectRadius:0.04});
  s.addText("Suitable for the route",{x:MX+7.7,y:1.83,w:3.7,h:0.35,fontSize:13,fontFace:T,color:DARK,bold:true,margin:0});
  s.addText("An A321XLR to New York needs circa 2,100 to 2,600 m at maximum take-off weight. Genoa's 2,915 m runway at sea level gives ample margin.",{x:MX+7.7,y:2.25,w:3.7,h:1.45,fontSize:11.5,fontFace:B,color:INK,margin:0,valign:"top"});
  pslot(s,MX+7.5,4.0,4.1,1.45,"Genoa airport / airfield aerial");
  src(s,"Genoa AIP (LIMJ); Invest in Genova (2025 traffic). Single-runway, no parallel."); footer(s);
}
// ============= SECTION 7 Methodology
divider("Section 7","Appendix: Methodology","");
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Forecast Methodology","Catchment recapture drives a point-to-point market");
  s.addText("Base demand is grown to maturity from Sabre O&D data, counting the Genoa catchment, with the leakage to Milan and other gateways recaptured by a local nonstop.",{x:MX,y:1.62,w:11.9,h:0.6,fontSize:12,fontFace:B,color:DARK2,margin:0,valign:"top"});
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX,y:2.4,w:5.7,h:3.45,fill:{color:LIGHT},line:{color:PANEL,width:1},rectRadius:0.04});
  s.addText("Catchment and Demand",{x:MX+0.25,y:2.55,w:5.2,h:0.35,fontSize:14,fontFace:T,color:DARK,bold:true,margin:0});
  bullets(s,MX+0.25,3.0,5.2,2.7,["Drive-time analysis sets Genoa's natural share of the Liguria market and the leakage to Milan.","Sabre O&D sizes the New York market from the catchment.","A bounded capture of the leaked pool gives the demand a nonstop recaptures."],11.5);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX+5.95,y:2.4,w:5.65,h:3.45,fill:{color:LIGHT},line:{color:PANEL,width:1},rectRadius:0.04});
  s.addText("Service and Revenue",{x:MX+6.2,y:2.55,w:5.2,h:0.35,fontSize:14,fontFace:T,color:DARK,bold:true,margin:0});
  bullets(s,MX+6.2,3.0,5.15,2.7,["The A321XLR is matched to peak demand on a seasonal, building pattern.","Revenue is built by cabin from MIDT fares, with cargo and ancillary added.","The relevance engine selects what matters for this profile: leisure, diaspora, cruise and the precedent, not corporate and tech."],11.5);
  src(s,"AviaSolutions analysis"); footer(s);
}
// CHOOSE GENOA
{ const s=pres.addSlide(); s.background={color:DARK};
  s.addText("Choose Genoa",{x:MX,y:0.7,w:11,h:0.6,fontSize:26,fontFace:T,color:WHITE,bold:true,margin:0});
  const pts=[["Largest Italian-American market","circa 2.6m in the New York metro, a deep year-round VFR base."],["Record tourism region","Liguria at 16.2m arrivals, the Cinque Terre and Portofino within an hour."],["Cruise homeport","circa 620,000 air-relevant embarkation passengers a year."],["The leakage to recapture","circa 92,500 New York passengers leaking out through Milan today."],["A proven template","United's A321XLR Newark nonstops to Palermo, Bari and Naples."],["Honest and conservative","a seasonal, building launch on a point-to-point market, cost base to be pressure-tested."]];
  pts.forEach(([t,d],i)=>{ const x=MX+(i%2)*5.95, y=1.65+Math.floor(i/2)*1.6; s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x,y,w:5.7,h:1.4,fill:{color:DARK2},line:{color:ORANGE,width:1},rectRadius:0.05}); s.addText(t,{x:x+0.25,y:y+0.15,w:5.2,h:0.4,fontSize:14,fontFace:T,color:ORANGE,bold:true,margin:0}); s.addText(d,{x:x+0.25,y:y+0.58,w:5.2,h:0.75,fontSize:11,fontFace:B,color:"D9E1EE",margin:0,valign:"top"}); });
  pg++; s.addText(String(pg),{x:W-1.0,y:Hh-0.36,w:0.5,h:0.26,fontSize:9,fontFace:B,color:"8FA0B3",align:"right",margin:0});
}
pres.writeFile({fileName:"GOA_v3.pptx"}).then(f=>console.log("Wrote",f));
