// Avia Solutions - BA LHR-SJC deck, built to the precise house template (spec v1).
// House style: UK English, no em/en dashes, "circa". Author Avia Solutions.
const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Avia Solutions";
pres.company = "Avia Solutions";
pres.title = "A Unique Opportunity to Serve Silicon Valley from London";

// ---- House palette (dark blue / cyan / orange) ----
const DARK="1F3864", DARK2="2E5496", CYAN="00B0F0", ORANGE="ED7D31", GREEN="70AD47";
const INK="3A3A3A", MUT="7F7F7F", WHITE="FFFFFF", LIGHT="F2F5F9", PANEL="E3E9F2", LINE="D4DCE6";
const T="Arial", B="Arial";
const W=13.333, Hh=7.5, MX=0.7;
const MAP="route_map_ba.png";
let pg=0;
const EVENT="World Routes 2026";

function header(s){
  s.addText("A Unique Opportunity to Serve Silicon Valley from London",{x:MX,y:0.16,w:8.5,h:0.25,fontSize:8.5,fontFace:B,color:MUT,margin:0,valign:"middle"});
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
  s.addText("FULL-BLEED IMAGE SLOT  (Silicon Valley / San Jose hero)",{x:0,y:1.35,w:W,h:0.3,fontSize:10,fontFace:B,color:"AEBED4",align:"center",italic:true,margin:0});
  s.addText("A Unique Opportunity to Serve\nSilicon Valley from London",{x:MX,y:3.35,w:11.8,h:1.5,fontSize:38,fontFace:T,color:WHITE,bold:true,margin:0,lineSpacingMultiple:1.02});
  s.addText("British Airways  |  London Heathrow - San Jose  |  Daily Boeing 787",{x:MX,y:5.05,w:11.8,h:0.4,fontSize:15,fontFace:B,color:CYAN,bold:true,margin:0});
  s.addText(EVENT,{x:MX,y:5.6,w:8,h:0.35,fontSize:13,fontFace:B,color:"C9D6E8",margin:0});
  s.addText("Prepared by Avia Solutions  |  June 2026",{x:MX,y:6.0,w:8,h:0.3,fontSize:11,fontFace:B,color:MUT,margin:0});
  s.addText("[ Airport logo ]      [ Avia Solutions logo ]      [ British Airways logo ]",{x:MX,y:6.7,w:11,h:0.35,fontSize:10,fontFace:B,color:MUT,italic:true,margin:0});
}
// ============= 2 CONTENTS
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s); title(s,"Contents");
  const items=[["1","Summary of Route Forecast","4"],["2","Why Silicon Valley","5"],["3","Tech Links: Silicon Valley and the UK","12"],["4","Stimulation, not Cannibalisation","16"],["5","London - San Jose Forecast","18"],["6","Revenue and Economics","24"],["7","San Jose Airport","28"],["8","Appendix: Methodology and Choose San Jose","31"]];
  let y=1.75; items.forEach(([n,t,p])=>{
    s.addText(n,{x:MX,y,w:0.6,h:0.5,fontSize:18,fontFace:T,color:ORANGE,bold:true,margin:0,valign:"top"});
    s.addText(t,{x:MX+0.75,y,w:10.2,h:0.5,fontSize:15,fontFace:B,color:DARK,bold:true,margin:0,valign:"top"});
    s.addText(p,{x:W-1.4,y,w:0.7,h:0.5,fontSize:13,fontFace:B,color:MUT,align:"right",margin:0,valign:"top"});
    y+=0.62; });
  footer(s);
}
// ============= 3 OVERVIEW (dense)
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"British Airways is well placed to serve the unserved London - Silicon Valley market");
  bullets(s,MX,1.65,6.05,5.4,[
    "SJC is the preferred gateway to Silicon Valley: 89% of businesses prefer SJC to SFO/OAK, and SJC is on average 40km closer than SFO to Fortune 500 companies (Apple HQ within 18km).",
    "San Jose is the wealthiest major metro in the US: median household income $175,491 versus the US average of circa $81,600.",
    "Silicon Valley is the global centre of the AI economy: the Bay Area took 60% of all global AI funding in 2025.",
    "Substantial premium and connecting demand over London to Europe, the Middle East and India.",
    "Large European and Indian populations in the San Jose catchment support strong VFR and one-stop demand.",
  ],11.5);
  bullets(s,MX+6.35,1.65,5.55,5.4,[
    "The US is the UK's largest single trading partner: $340bn two-way trade in 2024, services-led.",
    "London ranks first in Europe and fourth globally for technology; a record 150bn of US tech investment landed in the UK in 2025.",
    "A daily Boeing 787 forecast at circa 130,000 passengers and an 83.7% load factor in Year 1.",
    "No cannibalisation of SFO: a distinct South Bay catchment plus genuine market stimulation, proven by the ANA precedent.",
    "BA served this route in 2016-2020 and 2022-2023; the AI surge is what has changed since.",
  ],11.5);
  src(s,"AviaSolutions analysis; US Census ACS 2024; PitchBook-NVCA; ONS; Dealroom; gov.uk (2024-2026)"); footer(s);
}
// ============= 4 SUMMARY OF ROUTE FORECAST (MAP)
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Opportunity for British Airways: Summary of Route Forecast");
  // three figures
  const figs=[["Point to point market","249,800",DARK],["Connecting market over London","904,500",DARK2],["Connecting market over San Jose","1,206,800",CYAN]];
  figs.forEach(([l,v,c],i)=>{ const y=1.7+i*1.15;
    s.addText(v,{x:MX,y,w:3.3,h:0.6,fontSize:30,fontFace:T,color:c,bold:true,margin:0,valign:"middle"});
    s.addText(l,{x:MX,y:y+0.62,w:3.3,h:0.35,fontSize:11,fontFace:B,color:INK,margin:0,valign:"top"});
  });
  s.addText("* Based on AviaSolutions' San Jose Service Area catchment analysis",{x:MX,y:5.25,w:4,h:0.4,fontSize:8,fontFace:B,color:MUT,italic:true,margin:0});
  // map
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:4.3,y:1.62,w:8.3,h:3.55,fill:{color:LIGHT},line:{color:PANEL,width:1},rectRadius:0.04});
  s.addImage({path:MAP,x:4.4,y:1.7,w:8.1,h:3.4,sizing:{type:"cover",w:8.1,h:3.4}});
  // schedule options table
  s.addText("Schedule Options: Boeing 787-9",{x:MX,y:5.55,w:6,h:0.3,fontSize:12,fontFace:T,color:DARK,bold:true,margin:0});
  const sr=[["Sector","Dep.","Arr.","Op. Days","Aircraft","Seats","Annual Seats","Annual Pax","Seat Factor"].map(h=>hcell(h,h==="Sector"?"left":"center")),
    ["LHR-SJC","17:00","20:00","Daily","787-9","214","77,896","65,173",""].map((c,j)=>cell(c,j===0?"left":"center",0)),
    ["SJC-LHR","22:00","16:25","Daily","787-9","214","77,896","65,173",""].map((c,j)=>cell(c,j===0?"left":"center",1)),
    ["Total","","","7x weekly","787-9","","155,792","130,346","83.7%"].map((c,j)=>cell(c,j===0?"left":"center",0,true,DARK))];
  tbl(s,MX,5.88,11.9,sr,[1.3,0.85,0.85,1.2,1.1,0.95,1.6,1.5,1.55],9,0.32);
  footer(s);
}
// ============= SECTION 2 Why Silicon Valley
divider("Section 2","Why Silicon Valley","San Jose skyline");
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"SJC is the preferred gateway to Silicon Valley","Closer to the cluster, preferred by business, and uncongested");
  stat(s,MX,1.7,3.7,1.55,"89%","of businesses prefer SJC","over SFO and Oakland",DARK);
  stat(s,MX+3.95,1.7,3.7,1.55,"40km","closer than SFO","to Fortune 500 companies on average",DARK2);
  stat(s,MX+7.9,1.7,3.7,1.55,"18km","Apple global HQ","within 18km of SJC",CYAN);
  bullets(s,MX,3.55,7.4,2.6,[
    "SJC sits at the heart of Silicon Valley, circa 10 miles from the centre of the cluster; SFO is circa 29 miles away.",
    "No congestion and no onward ground travel for Valley-bound passengers, unlike SFO or Oakland.",
    "Increasingly served by premium carriers, with a modern international arrivals facility.",
  ],12);
  pslot(s,MX+7.7,3.55,3.9,2.6,"SJC terminal / Silicon Valley map"); src(s,"AviaSolutions analysis; SJC airport"); footer(s);
}
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"The wealthiest, most innovative metro in the US","A premium catchment for a high-yield London service");
  stat(s,MX,1.7,2.85,1.55,"$175,491","Median household income","#1 of the 50 largest US metros",DARK);
  stat(s,MX+3.05,1.7,2.85,1.55,"$171,660","GDP per capita","Highest of any US metro",DARK2);
  stat(s,MX+6.1,1.7,2.85,1.55,"No. 1","US city for patents","200,778 granted 2020-2024",CYAN);
  stat(s,MX+9.15,1.7,2.45,1.55,"44.9%","of US venture capital","San Francisco metro, 2025",ORANGE);
  bullets(s,MX,3.5,11.9,2.4,[
    "San Jose - Sunnyvale - Santa Clara is the richest major metro in the country, roughly double the national median household income.",
    "The San Jose - San Francisco cluster has ranked first in the world for innovation for six consecutive years (WIPO 2025).",
    "An unmatched concentration of global technology headquarters, led by Apple, Alphabet and NVIDIA.",
  ],12.5);
  src(s,"US Census ACS 2024; BEA; USPTO / CommercialCafe; PitchBook-NVCA (Jan 2026); WIPO GII 2025"); footer(s);
}
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"The AI capital: what has changed since 2023","The strongest current reason a premium London service works");
  stat(s,MX,1.7,3.55,1.55,"$126bn","Global AI funding to the Bay Area","60% of the world total, 2025",DARK);
  stat(s,MX+3.75,1.7,3.55,1.55,"81%","of Bay Area startup capital","went into AI in 2025",DARK2);
  stat(s,MX+7.5,1.7,3.55,1.55,"up to $100bn","NVIDIA commitment to OpenAI","announced September 2025",ORANGE);
  bullets(s,MX,3.5,7.4,2.5,[
    "Silicon Valley is the undisputed global centre of the AI industry; AI start-ups raised $211bn worldwide in 2025.",
    "These fast-scaling, capital-rich, internationally connected firms are exactly the premium long-haul demand a London service targets.",
    "When BA last served the route this economy did not exist at today's scale.",
  ],12);
  pslot(s,MX+7.7,3.5,3.9,2.5,"NVIDIA campus, Santa Clara"); src(s,"Crunchbase / HumanX (Feb 2026); NVIDIA; PitchBook-NVCA"); footer(s);
}
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"The headquarters are on the airport's doorstep","San Jose is inside the cluster, not adjacent to it");
  const rows=[["Company","Location","From SJC"].map(h=>hcell(h,h==="From SJC"?"right":"left")),
    ...[["NVIDIA","Santa Clara","circa 4 miles"],["Apple (Apple Park)","Cupertino","circa 9 miles"],["Google / Alphabet","Mountain View","circa 12 miles"],["Adobe, eBay, PayPal, Cisco","San Jose","minutes"],["Meta","Menlo Park","circa 18 miles"]].map((r,i)=>r.map((c,j)=>cell(c,j===2?"right":"left",i)))];
  tbl(s,MX,1.7,6.3,rows,[2.7,2.0,1.6],11,0.42);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX,y:4.55,w:6.3,h:1.2,fill:{color:LIGHT},line:{color:ORANGE,width:1},rectRadius:0.04});
  s.addText("SJC is circa 19 miles closer to the centre of Silicon Valley than SFO, the airport inside the densest tech cluster on earth.",{x:MX+0.2,y:4.65,w:5.9,h:1.0,fontSize:12,fontFace:B,color:INK,valign:"middle",margin:0});
  pslot(s,MX+6.6,1.7,2.45,2.0,"Google / San Jose"); pslot(s,MX+9.15,1.7,2.45,2.0,"Apple Park");
  pslot(s,MX+6.6,3.8,5.0,1.95,"NVIDIA HQ, Santa Clara");
  src(s,"Company sites; Santa Clara County; Visit San Jose (2026)"); footer(s);
}
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"A premium, India-connected catchment","Strong VFR and one-stop India demand over London");
  stat(s,MX,1.7,3.55,1.55,"209,006","Asian Indian residents","San Jose metro, circa 10.5%",DARK);
  stat(s,MX+3.75,1.7,3.55,1.55,"No. 1","US county for Indian immigrants","Santa Clara County",DARK2);
  stat(s,MX+7.5,1.7,3.55,1.55,"circa 73%","of Bay Area H-1B workers","Indian-born, high-yield",CYAN);
  bullets(s,MX,3.5,11.9,2.4,[
    "One of the densest Indian-American concentrations of any US metro, high-income and degree-educated.",
    "Supports VFR travel and one-stop India connectivity over London, feeding Delhi, Mumbai, Bengaluru and Hyderabad.",
    "India demand is excluded from the base forecast to stay conservative, so it sits as upside.",
  ],12.5);
  src(s,"US Census ACS 2024; Migration Policy Institute; Pew Research; USCIS / NFAP"); footer(s);
}
// ============= SECTION 3 Tech links
divider("Section 3","Tech Links: Silicon Valley and the UK","London tech quarter");
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"London is a genuine peer, not a spoke","Bay Area firms are building their largest non-US bases in London");
  stat(s,MX,1.7,3.55,1.55,"1st","in Europe for tech","4th globally (Dealroom 2026)",DARK);
  stat(s,MX+3.75,1.7,3.55,1.55,"150bn","record US investment","UK-US State Visit, Sept 2025",DARK2);
  stat(s,MX+7.5,1.7,3.55,1.55,"565,000 sq ft","London office space","taken by AI firms, early 2026",ORANGE);
  bullets(s,MX,3.5,11.9,2.5,[
    "Named US tech investment into the UK in 2025: Microsoft 22bn, NVIDIA 11bn, Google 5bn, plus Salesforce and CoreWeave.",
    "OpenAI has made London its largest research hub outside the US; Anthropic has taken its first permanent London office.",
    "London raised circa 13.2bn of tech venture funding in 2025 and is home to 138 unicorns, the largest ecosystem in Europe.",
  ],12.5);
  src(s,"Dealroom 2026; gov.uk State Visit (Sept 2025); CNBC (Jun 2026); techUK"); footer(s);
}
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Life sciences and a tech corridor on Heathrow's doorstep","The demand sits on the Heathrow side of London");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX,y:1.7,w:5.7,h:3.9,fill:{color:LIGHT},line:{color:PANEL,width:1},rectRadius:0.04});
  s.addText("The Golden Triangle",{x:MX+0.25,y:1.85,w:5.2,h:0.35,fontSize:14,fontFace:T,color:DARK,bold:true,margin:0});
  bullets(s,MX+0.25,2.3,5.2,3.1,["London - Oxford - Cambridge: circa 57% of UK biopharma employment, ranked third in the world among life-science hubs.","The Francis Crick Institute is Europe's largest single biomedical laboratory.","US capital is flowing in: Prologis committed circa 3.9bn including a Cambridge Biomedical Campus expansion."],11);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX+5.95,y:1.7,w:5.65,h:3.9,fill:{color:LIGHT},line:{color:PANEL,width:1},rectRadius:0.04});
  s.addText("The Thames Valley",{x:MX+6.2,y:1.85,w:5.2,h:0.35,fontSize:14,fontFace:T,color:DARK,bold:true,margin:0});
  bullets(s,MX+6.2,2.3,5.15,3.1,["The M4 corridor west of Heathrow hosts Microsoft, Oracle, Cisco, NVIDIA, SAP and Dell UK operations.","Slough holds the largest data-centre concentration in Europe.","Many of these Bay Area firms located here for Heathrow access, so the demand is on the airport's doorstep."],11);
  src(s,"DTRE / Lightcast / Savills 2025; Francis Crick Institute; gov.uk; RWA Consultants"); footer(s);
}
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Trade and travel underpin the corridor","The densest services and digital trade relationship in the world");
  stat(s,MX,1.7,2.85,1.55,"$340bn","US-UK trade","Two-way, 2024",DARK);
  stat(s,MX+3.05,1.7,2.85,1.55,"137bn","UK services exports to US","2024",DARK2);
  stat(s,MX+6.1,1.7,2.85,1.55,"20.59m","US-UK air passengers","Largest US-Europe market, 2024",CYAN);
  stat(s,MX+9.15,1.7,2.45,1.55,"$1.7tn+","two-way FDI","Each other's largest partner",ORANGE);
  bullets(s,MX,3.5,11.9,2.4,[
    "Heavily services-weighted, the strongest evidence that trade drives business travel. California's top UK export line is computers and electronics.",
    "The UK is the largest US-Europe market and Heathrow the top US foreign gateway; Bay Area demand is funnelled through SFO today.",
    "Deep both ways: 5.6m US visitors to the UK and 4.04m UK visitors to the US in 2024.",
  ],12.5);
  src(s,"USTR; ONS 2024; BEA; US DOT 2024; VisitBritain; US NTTO"); footer(s);
}
// ============= SECTION 4 Stimulation
divider("Section 4","Stimulation, not Cannibalisation","ANA 787 at San Jose");
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"A new SJC service grows the market, it does not cannibalise SFO","Proven by the ANA Silicon Valley - Tokyo precedent");
  bullets(s,MX,1.7,7.2,3.6,[
    "ANA launched San Jose - Tokyo in January 2013, the first ever nonstop between Silicon Valley and Japan, configured for premium corporate demand.",
    "Over 13 years of Bay Area - Tokyo service the SJC launch was entirely additional traffic: it grew the overall market and did not cannibalise the SFO service.",
    "San Jose anchors a distinct South Bay catchment, on average 40km closer to the Valley's headquarters than SFO.",
    "Peer-reviewed work confirms a new nonstop both recaptures connecting demand and stimulates genuinely new point-to-point traffic.",
  ],12);
  stat(s,MX+7.5,1.7,4.1,1.7,"Additional","not diverted","ANA-SJC grew the Bay-Tokyo market",DARK);
  pslot(s,MX+7.5,3.6,4.1,1.7,"ANA / ZIPAIR 787 at SJC");
  src(s,"AviaSolutions analysis; ANA; Journal of Air Transport Management vol. 98 (2022)"); footer(s);
}
// ============= SECTION 5 Forecast
divider("Section 5","London - San Jose Forecast","Catchment map");
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"San Jose Catchment Area","Primary, secondary and contested service zones");
  const cards=[["Primary","San Jose is the most convenient airport on surface access; the core of the demand.",DARK],["Secondary","Extends south and east; passengers drive past SJC to SFO today and would switch given a nonstop.",DARK2],["Contested","To the north-west, equal drive time to SJC and SFO; shared with San Francisco.",CYAN]];
  cards.forEach(([t,d,c],i)=>{ const x=MX+i*3.95;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x,y:1.7,w:3.7,h:2.1,fill:{color:WHITE},line:{color:c,width:1.5},rectRadius:0.05,shadow:sh()});
    s.addText(t,{x:x+0.2,y:1.88,w:3.3,h:0.45,fontSize:16,fontFace:T,color:c,bold:true,margin:0});
    s.addText(d,{x:x+0.2,y:2.4,w:3.3,h:1.3,fontSize:11,fontFace:B,color:INK,margin:0,valign:"top"}); });
  pslot(s,MX,4.0,11.9,1.5,"SJC drive-time catchment map (primary / secondary / contested)");
  src(s,"AviaSolutions San Jose Service Area catchment analysis"); footer(s);
}
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Key traffic flows from the San Jose catchment, beyond London","Annual two-way demand to points over Heathrow");
  s.addChart(pres.charts.BAR,[{name:"Annual demand",labels:["Paris","Frankfurt","Amsterdam","Tel Aviv","Munich","Zurich","Copenhagen","Rome","Stockholm","Madrid"],values:[140521,100810,60675,45892,43810,36924,32449,27549,25155,19730]}],{x:MX,y:1.7,w:11.9,h:4.0,barDir:"col",chartColors:[DARK2],showValue:true,dataLabelPosition:"outEnd",dataLabelColor:INK,dataLabelFontSize:9,dataLabelFontFace:B,catAxisLabelColor:MUT,valAxisLabelColor:MUT,catAxisLabelFontSize:10,valGridLine:{color:PANEL,size:0.5},catGridLine:{style:"none"},showLegend:false,chartArea:{fill:{color:WHITE}}});
  src(s,"AviaSolutions QSI connecting-demand model (Sabre MI). Validated reference case."); footer(s);
}
// MAIN FORECAST TABLE
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Route Forecast British Airways: London - San Jose (Daily Service)");
  const hd=["Market","Base Demand (000s)","Growth","Demand 2016 (000s)","Stim.","After Stim. (000s)","BA Capture","Forecast (000s)","PDEW"].map((h,j)=>hcell(h,j===0?"left":"right"));
  const data=[
    ["UK Business","71.4","3.0%","77.9","x1.15","89.6","40.0%","35.8","49.2"],
    ["UK Leisure / VFR - Primary","36.4","3.0%","39.7","-","39.7","20.0%","7.9","10.9"],
    ["UK Leisure / VFR - Secondary","17.4","3.0%","19.0","-","19.0","20.0%","3.8","5.2"],
    ["UK Leisure / VFR - Contested","4.6","3.0%","5.0","-","5.0","5.0%","0.3","0.3"],
    ["US Business","65.9","3.0%","71.9","x1.15","82.7","22.0%","18.2","25.0"],
    ["US Leisure / VFR - Primary","33.6","2.4%","36.1","-","36.1","30.0%","10.8","14.9"],
    ["US Leisure / VFR - Secondary","16.1","2.4%","17.3","-","17.3","30.0%","5.2","7.1"],
  ];
  const rows=[hd]; data.forEach((r,i)=>rows.push(r.map((c,j)=>cell(c,j===0?"left":"right",i))));
  rows.push(["Point to Point Total","249.8","","271.5","","293.9","28.1%","82.7","113.6"].map((c,j)=>cell(c,j===0?"left":"right",0,true,DARK)));
  rows.push(["Connecting at London","991.3","","","","","4.5%","45.0","61.8"].map((c,j)=>cell(c,j===0?"left":"right",1)));
  rows.push(["Connecting at San Jose","1,206.8","","","","","0.2%","2.6","3.6"].map((c,j)=>cell(c,j===0?"left":"right",0)));
  rows.push(["Total Forecast","","","","","","","130.3","178.6"].map((c,j)=>cell(c,j===0?"left":"right",1,true,DARK)));
  tbl(s,MX,1.65,11.9,rows,[2.85,1.25,0.85,1.35,0.75,1.35,1.05,1.15,0.85],8.5,0.36);
  s.addText("Year 1 (2016 service year), 214-seat Boeing 787, 83.7% load factor on 155,792 annual seats. India connecting demand excluded to stay conservative.",{x:MX,y:5.95,w:11.9,h:0.35,fontSize:9.5,fontFace:B,color:DARK2,italic:true,margin:0});
  src(s,"AviaSolutions QSI forecast model (validated reference case), to be refreshed on the live 2024-2025 base"); footer(s);
}
// CONNECTING AT LONDON
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Route Forecast: Passengers Connecting at London");
  const cities=[["1","PAR","Paris","France","140,521","3.0%","4,216","5.8"],["2","DUB","Dublin","Ireland","28,174","9.0%","2,536","3.5"],["3","MUC","Munich","Germany","43,810","5.4%","2,366","3.2"],["4","CPT","Cape Town","South Africa","5,893","37.5%","2,212","3.0"],["5","FRA","Frankfurt","Germany","100,810","2.0%","2,016","2.8"],["6","DUS","Dusseldorf","Germany","13,088","13.7%","1,793","2.5"],["7","AMS","Amsterdam","Netherlands","60,675","2.9%","1,767","2.4"],["8","STO","Stockholm","Sweden","25,155","6.2%","1,555","2.1"],["9","GVA","Geneva","Switzerland","12,128","12.6%","1,531","2.1"],["10","HEL","Helsinki","Finland","6,606","19.6%","1,294","1.8"],["11","CAI","Cairo","Egypt","5,501","23.5%","1,294","1.8"],["12","MIL","Milan","Italy","19,567","6.5%","1,278","1.8"],["13","BER","Berlin","Germany","18,020","7.0%","1,269","1.7"],["14","GLA","Glasgow","UK","4,028","30.3%","1,219","1.7"],["15","CPH","Copenhagen","Denmark","32,449","3.6%","1,173","1.6"]];
  const hd=["Nr","Code","City","Country","Demand 2016","BA Share","Forecast","PDEW"].map((h,j)=>hcell(h,(j>=4)?"right":"left"));
  const rows=[hd]; cities.forEach((r,i)=>rows.push(r.map((c,j)=>cell(c,(j>=4)?"right":"left",i))));
  rows.push(["","","Total (all markets)","","991,343","4.5%","45,011","61.8"].map((c,j)=>cell(c,(j>=4)?"right":"left",0,true,DARK)));
  tbl(s,MX,1.6,11.9,rows,[0.6,0.9,2.1,2.0,1.6,1.2,1.3,0.9],8.5,0.27);
  src(s,"AviaSolutions QSI connecting-demand model (Sabre MI). Top markets shown; full list circa 70 cities."); footer(s);
}
// CONNECTING AT SAN JOSE
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Route Forecast: Passengers Connecting at San Jose");
  const cities=[["1","OGG","Kahului (Maui)","USA","6,237","16.0%","1,000","1.4"],["2","KOA","Kona","USA","4,815","10.1%","485","0.7"],["3","SEA","Seattle","USA","162,580","0.2%","383","0.5"],["4","LAX","Los Angeles","USA","794,266","0.0%","346","0.5"],["5","RNO","Reno","USA","6,325","1.5%","98","0.1"],["6","SLC","Salt Lake City","USA","35,222","0.3%","98","0.1"],["7","PHX","Phoenix","USA","108,939","0.1%","91","0.1"],["8","PDX","Portland","USA","39,449","0.2%","86","0.1"],["9","GDL","Guadalajara","Mexico","8,999","0.4%","37","0.1"]];
  const hd=["Nr","Code","City","Country","Demand 2016","BA Share","Forecast","PDEW"].map((h,j)=>hcell(h,(j>=4)?"right":"left"));
  const rows=[hd]; cities.forEach((r,i)=>rows.push(r.map((c,j)=>cell(c,(j>=4)?"right":"left",i))));
  rows.push(["","","Total over San Jose","","1,206,843","0.2%","2,628","3.6"].map((c,j)=>cell(c,(j>=4)?"right":"left",0,true,DARK)));
  tbl(s,MX,1.7,8.6,rows,[0.55,0.85,2.0,1.3,1.45,1.1,1.1,0.85],9,0.34);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX+8.9,y:1.7,w:2.7,h:3.6,fill:{color:LIGHT},line:{color:PANEL,width:1},rectRadius:0.04});
  s.addText("San Jose is an origin and destination market, not a connecting hub, so onward demand adds a modest layer beyond strong Hawaii leisure flows.",{x:MX+9.05,y:1.9,w:2.4,h:3.2,fontSize:11,fontFace:B,color:INK,margin:0,valign:"top"});
  src(s,"AviaSolutions QSI connecting-demand model (Sabre MI)"); footer(s);
}
// ============= SECTION 6 Economics
divider("Section 6","Revenue and Economics","787 cabin");
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Revenue Forecast for London - San Jose (Daily Service)");
  const yrs=["Year 1","Year 2","Year 3"];
  const rows=[["",...yrs].map((h,j)=>hcell(h,j===0?"left":"right"))];
  const add=(l,v,bold)=>rows.push([l,...v].map((c,j)=>cell(c,j===0?"left":"right",rows.length,bold,bold?DARK:INK)));
  add("Passengers - Point to Point",["82,708","85,106","87,574"]);
  add("Passengers - Connecting at London",["45,011","46,316","47,659"]);
  add("Passengers - Connecting at San Jose",["2,628","2,704","2,782"]);
  add("Total Passengers",["130,346","134,126","138,016"],true);
  add("Annual Capacity",["155,792","155,792","155,792"]);
  add("Implied Load Factor",["83.7%","86.1%","88.6%"],true);
  add("Revenue - Point to Point",["$84.6m","$87.1m","$89.6m"]);
  add("Revenue - Connecting at London",["$26.6m","$27.4m","$28.2m"]);
  add("Revenue - Connecting at San Jose",["$2.1m","$2.2m","$2.2m"]);
  add("Revenue - Cargo",["$7.3m","$7.6m","$8.0m"]);
  add("Revenue - Ancillary",["$1.0m","$1.1m","$1.1m"]);
  add("Total Revenue",["$121.7m","$125.4m","$129.2m"],true);
  tbl(s,MX,1.65,11.9,rows,[5.0,2.3,2.3,2.3],9.5,0.33);
  src(s,"AviaSolutions QSI revenue model (validated reference case). Years relabelled from the 2016-2018 reference."); footer(s);
}
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Market Forecast Scenario: London - San Jose","The full economic picture for the airline business case");
  const m=[["Equipment","Boeing 787-9"],["Weekly departures","7"],["Total departures (annual, two-way)","728"],["Block hours per departure","circa 10.6"],["Business cabin seats","50"],["Premium coach seats","39"],["Coach seats","125"],["Total seats","214"],["Business cabin load factor","78%"],["Total load factor","83.7%"],["Average one-way P2P fare","$1,820"],["Average one-way connecting fare","$1,150"],["Average one-way fare (blended)","$1,640"],["Yield (Rev/RPK)","$0.101"],["PRASK","$0.085"],["Passenger revenue","$113.4m"],["Cargo revenue","$7.3m"],["Ancillary revenue","$1.0m"],["Total revenue","$121.7m"],["TRASK","$0.091"]];
  const half=Math.ceil(m.length/2);
  const L=[["Metric","Year 1"].map(h=>hcell(h,h==="Metric"?"left":"right"))]; m.slice(0,half).forEach((r,i)=>L.push(r.map((c,j)=>cell(c,j===0?"left":"right",i))));
  const R=[["Metric","Year 1"].map(h=>hcell(h,h==="Metric"?"left":"right"))]; m.slice(half).forEach((r,i)=>R.push(r.map((c,j)=>cell(c,j===0?"left":"right",i))));
  tbl(s,MX,1.7,5.75,L,[3.9,1.85],9.5,0.41); tbl(s,MX+6.15,1.7,5.75,R,[3.9,1.85],9.5,0.41);
  src(s,"AviaSolutions revenue and aircraft economics model. Illustrative; to be refreshed on the live base."); footer(s);
}
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Revenue Build Up by Flow and by Cabin");
  s.addText("Revenue build up by flow ($m)",{x:MX,y:1.55,w:5.5,h:0.3,fontSize:12,fontFace:T,color:DARK,bold:true,margin:0});
  s.addChart(pres.charts.BAR,[{name:"Point to point",labels:["Yr1","Yr2","Yr3"],values:[84.6,87.1,89.6]},{name:"Connecting London",labels:["Yr1","Yr2","Yr3"],values:[26.6,27.4,28.2]},{name:"Connecting SJC",labels:["Yr1","Yr2","Yr3"],values:[2.1,2.2,2.2]},{name:"Cargo & ancillary",labels:["Yr1","Yr2","Yr3"],values:[8.3,8.7,9.1]}],{x:MX,y:1.9,w:5.75,h:3.9,barDir:"col",barGrouping:"stacked",chartColors:[DARK,DARK2,CYAN,ORANGE],showLegend:true,legendPos:"b",legendFontSize:8,legendColor:MUT,catAxisLabelColor:MUT,valAxisLabelColor:MUT,valGridLine:{color:PANEL,size:0.5},catGridLine:{style:"none"},chartArea:{fill:{color:WHITE}}});
  s.addText("Revenue build up by cabin ($m)",{x:MX+6.15,y:1.55,w:5.5,h:0.3,fontSize:12,fontFace:T,color:DARK,bold:true,margin:0});
  s.addChart(pres.charts.BAR,[{name:"Business",labels:["Yr1","Yr2","Yr3"],values:[60.0,61.8,63.6]},{name:"Premium coach",labels:["Yr1","Yr2","Yr3"],values:[22.0,22.7,23.4]},{name:"Coach",labels:["Yr1","Yr2","Yr3"],values:[31.4,32.4,33.3]}],{x:MX+6.15,y:1.9,w:5.75,h:3.9,barDir:"col",barGrouping:"stacked",chartColors:[DARK,CYAN,GREEN],showLegend:true,legendPos:"b",legendFontSize:8,legendColor:MUT,catAxisLabelColor:MUT,valAxisLabelColor:MUT,valGridLine:{color:PANEL,size:0.5},catGridLine:{style:"none"},chartArea:{fill:{color:WHITE}}});
  src(s,"AviaSolutions revenue model. Illustrative split by flow and cabin."); footer(s);
}
// ============= SECTION 7 Airport
divider("Section 7","San Jose Airport","SJC terminal at dusk");
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"A world-class airport at the centre of the Valley","Closer to the cluster and more reliable than SFO");
  stat(s,MX,1.7,3.55,1.55,"11.85m","passengers in 2024","Silicon Valley's home airport",DARK);
  stat(s,MX+3.75,1.7,3.55,1.55,"36 gates","two terminals","International arrivals, Global Entry",DARK2);
  stat(s,MX+7.5,1.7,3.55,1.55,"787-ready","widebody capable","ZIPAIR 787 to Tokyo today",CYAN);
  bullets(s,MX,3.5,7.4,2.5,[
    "SJC has handled 787, A340 and larger widebodies; a daily 787 is well within capability.",
    "A genuine reliability advantage over SFO, which loses half its arrival rate in fog while SJC is unaffected.",
    "A BA service would be the only Europe nonstop at the airport.",
  ],12);
  pslot(s,MX+7.7,3.5,3.9,2.5,"SJC terminal / 787 at gate");
  src(s,"SJC activity report (CY2024); Cranky Flier (2026)"); footer(s);
}
{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
  title(s,"Airport support behind a returning service","A de-risked launch, backed by the airport");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX,y:1.7,w:7.4,h:3.7,fill:{color:LIGHT},line:{color:PANEL,width:1},rectRadius:0.04});
  s.addText("What the airport brings",{x:MX+0.25,y:1.85,w:6.9,h:0.35,fontSize:14,fontFace:T,color:DARK,bold:true,margin:0});
  bullets(s,MX+0.25,2.35,6.9,2.9,[
    "An Air Service Development programme designed to encourage incremental airline route decisions.",
    "Concrete commitment: when BA exited in 2023, SJC offered a $303,700 credit toward a future contract.",
    "The airport is actively seeking international partners, and a London link is its clearest gap.",
    "Marketing support and incentive terms to be confirmed with the airport for the live tariff.",
  ],12);
  stat(s,MX+7.7,1.7,3.9,1.75,"$303,700","resumption credit offered","the airport's commitment",ORANGE);
  pslot(s,MX+7.7,3.65,3.9,1.75,"Airport / air service team");
  src(s,"SJC Air Service Development; Simple Flying (Mar 2025)"); footer(s);
}
// ============= SECTION 8 Methodology / Appendix
divider("Section 8","Appendix: Methodology","");
{ const meth=[
   ["Summary of Forecast Methodology",["Base traffic demand is grown to maturity using Sabre MI O&D data, adjusted for non-MIDT booking channels.","Only passengers from the San Jose Service Area are counted, for both point-to-point and connecting traffic beyond the hub.","Point-to-point demand is split into business and leisure/VFR, with growth rates from GDP, trade and econometric forecasts.","Connectivity considers the airline's subsidiaries and alliance partners."]],
   ["Schedules",["The forecast assumes a specific schedule: outbound and return timings, layover and elapsed times.","A daily (7x weekly) frequency on a 214-seat Boeing 787.","Schedule quality drives the QSI competition against all existing one-stop options."]],
   ["Point to Point Methodology",["Sabre MI provides the historic O&D market between the catchment and London.","A compound annual growth rate grows the market to the service year.","Stimulation from the new direct service is applied from industry analysis and historical benchmarks.","Capture rates are set from frequency-share analysis and traffic-leakage estimates."]],
   ["Connecting Markets Methodology",["Sabre MI provides the connecting markets over the hub, excluding double connections.","Demand is grown to maturity on the same basis as point-to-point.","A Quality of Service Index allocates demand across competing itineraries.","The QSI scores total elapsed time, connection type (online, interline, codeshare/alliance) and frequency."]],
   ["Revenue Forecast Methodology",["Passenger growth follows the QSI forecast.","Fares come from MIDT data, weighted down with a business-fare reduction and split by cabin, with spill traffic estimated.","Cargo revenue is built from aircraft belly capacity at conservative yields, benchmarked to volume.","Ancillary revenue is sourced from industry reports."]],
  ];
  meth.forEach(([t,items])=>{ const s=pres.addSlide(); s.background={color:WHITE}; header(s);
    title(s,t,"AviaSolutions QSI route forecast methodology");
    bullets(s,MX,1.75,11.9,4.6,items,13); src(s,"AviaSolutions analysis"); footer(s); });
}
// CHOOSE SAN JOSE
{ const s=pres.addSlide(); s.background={color:DARK};
  s.addText("Choose San Jose",{x:MX,y:0.7,w:11,h:0.6,fontSize:26,fontFace:T,color:WHITE,bold:true,margin:0});
  const pts=[["Premium market","The wealthiest, most innovative and most AI-intensive metro in the world."],["Underserved","No direct daily London service today; demand is funnelled through SFO."],["Net-new traffic","A distinct South Bay catchment that grows the market rather than cannibalising SFO."],["Conservative forecast","circa 130,000 passengers at 83.7% load factor, with India and US point-of-sale upside excluded."],["Airport support","Active air-service development and a proven incentive commitment."],["Two genuine tech centres","London and Silicon Valley, a two-way premium corridor."]];
  pts.forEach(([t,d],i)=>{ const x=MX+(i%2)*5.95, y=1.65+Math.floor(i/2)*1.6;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x,y,w:5.7,h:1.4,fill:{color:DARK2},line:{color:ORANGE,width:1},rectRadius:0.05});
    s.addText(t,{x:x+0.25,y:y+0.15,w:5.2,h:0.4,fontSize:14,fontFace:T,color:ORANGE,bold:true,margin:0});
    s.addText(d,{x:x+0.25,y:y+0.58,w:5.2,h:0.75,fontSize:11,fontFace:B,color:"D9E1EE",margin:0,valign:"top"}); });
  pg++; s.addText(String(pg),{x:W-1.0,y:Hh-0.36,w:0.5,h:0.26,fontSize:9,fontFace:B,color:"8FA0B3",align:"right",margin:0});
}
// THANK YOU
{ const s=pres.addSlide(); s.background={color:DARK};
  s.addText("Thank you",{x:MX,y:2.3,w:11,h:1.0,fontSize:44,fontFace:T,color:WHITE,bold:true,margin:0});
  s.addText("Re-establishing the link between London and Silicon Valley",{x:MX,y:3.5,w:11,h:0.6,fontSize:18,fontFace:B,color:CYAN,margin:0});
  s.addText([{text:"Avia Solutions",options:{bold:true,color:ORANGE,fontSize:15,breakLine:true}},{text:"Route development and air service consultancy",options:{color:"AEBED4",fontSize:12,breakLine:true}},{text:"john.carter@aviasolutions.com",options:{color:"AEBED4",fontSize:12}}],{x:MX,y:4.6,w:8,h:1.1,fontFace:B,margin:0,valign:"top"});
  pg++; s.addText(String(pg),{x:W-1.0,y:Hh-0.36,w:0.5,h:0.26,fontSize:9,fontFace:B,color:"8FA0B3",align:"right",margin:0});
}

pres.writeFile({fileName:"BA_LHR-SJC_Route_Business_Case_v2.pptx"}).then(f=>console.log("Wrote",f));
