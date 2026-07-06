const fs=require("fs");
const {Document,Packer,Paragraph,TextRun,Table,TableRow,TableCell,HeadingLevel,
 BorderStyle,WidthType,ShadingType,AlignmentType}=require("docx");
const CW=9026;
const bd={style:BorderStyle.SINGLE,size:1,color:"BBBBBB"};
const B={top:bd,bottom:bd,left:bd,right:bd};
const M={top:60,bottom:60,left:110,right:110};
function P(runs,opts){opts=opts||{};return new Paragraph({spacing:{after:opts.after==null?120:opts.after},children:Array.isArray(runs)?runs:[new TextRun(runs)]});}
function H1(s){return new Paragraph({heading:HeadingLevel.HEADING_1,children:[new TextRun(s)]});}
function note(s){return new Paragraph({spacing:{after:140},children:[new TextRun({text:s,italics:true,size:19,color:"595959"})]});}
function cell(t,w,o){o=o||{};return new TableCell({borders:B,width:{size:w,type:WidthType.DXA},margins:M,
 children:[new Paragraph({alignment:o.right?AlignmentType.RIGHT:AlignmentType.LEFT,children:[new TextRun({text:t,bold:!!o.bold,size:20})]})]});}
function hcell(h,w,i){return new TableCell({borders:B,width:{size:w,type:WidthType.DXA},margins:M,
 shading:{fill:"1F3864",type:ShadingType.CLEAR},
 children:[new Paragraph({alignment:i>0?AlignmentType.RIGHT:AlignmentType.LEFT,children:[new TextRun({text:h,bold:true,color:"FFFFFF",size:20})]})]});}
function table(headers,rows,widths){
 const trs=[new TableRow({children:headers.map((h,i)=>hcell(h,widths[i],i))})];
 rows.forEach(r=>{trs.push(new TableRow({children:r.map((c,i)=>cell(String(c),widths[i],{right:i>0,bold:r._b}))}));});
 return new Table({width:{size:CW,type:WidthType.DXA},columnWidths:widths,rows:trs});
}
function brow(a){a._b=true;return a;}
function run(b,t){return new TextRun({text:t,bold:!!b});}

const doc=new Document({
 creator:"Avia Solutions",lastModifiedBy:"Avia Solutions",
 title:"Genoa-New York Sabre O&D analysis",description:"Italy-NYC O&D pack",
 styles:{default:{document:{run:{font:"Arial",size:21}}},paragraphStyles:[
  {id:"Heading1",name:"Heading 1",basedOn:"Normal",next:"Normal",quickFormat:true,
   run:{size:24,bold:true,font:"Arial",color:"1F3864"},paragraph:{spacing:{before:220,after:100},outlineLevel:0}}]},
 sections:[{properties:{page:{size:{width:11906,height:16838},margin:{top:1440,right:1440,bottom:1440,left:1440}}},children:[
  new Paragraph({spacing:{after:40},children:[new TextRun({text:"Genoa-New York: Italy-NYC O&D analysis",bold:true,size:32,color:"1F3864"})]}),
  new Paragraph({spacing:{after:30},children:[new TextRun({text:"Sabre MIDT O&D, full years 2025 and 2024. Avia Solutions, prepared 26 June 2026 for the call of 29 June 2026.",size:20,color:"595959"})]}),
  new Paragraph({spacing:{after:160},children:[new TextRun({text:"Basis and flags: all volumes are bidirectional O&D, both directions combined. NYC = JFK + EWR + LGA. 2025 is the Sabre Best estimate file, so read year-on-year as direction of travel, not audited actuals. Point of sale is shown as point of origin country (the data carries true journey origin, not ticket-sale location). Yield is passenger-weighted revenue per O&D passenger. Seasonality (section 4) and the point-of-sale catchment floor (section 7) come from a separate Sabre point-of-sale extract for Milan-NYC covering March 2025 to February 2026.",size:19,color:"595959"})]}),

  H1("1. Italy-NYC O&D by origin airport"),
  note("Total annual O&D between each Italian airport and New York, both directions."),
  table(["Origin airport","2025","2024"],[
   ["Rome FCO","823,474","875,003"],["Milan MXP","708,445","754,649"],["Venice VCE","179,983","190,479"],
   ["Naples NAP","151,275","156,579"],["Bologna BLQ","53,061","47,511"],["Milan LIN","47,295","37,389"],
   ["Genoa GOA","9,278","8,276"],["Other Italian airports","394,071","334,976"],
   brow(["Italy total","2,366,882","2,404,861"])],[3626,2700,2700]),

  H1("2. Milan Malpensa-NYC routing"),
  note("How Milan-NYC O&D splits between nonstop and connecting service, both directions, 2025."),
  table(["Milan MXP-NYC, 2025","Passengers","Share"],[
   ["Direct (nonstop)","648,383","92%"],["Connecting via European hubs","60,062","8%"],
   brow(["Total","708,445","100%"])],[4626,2200,2200]),
  P([run(1,"Largest nonstop operators, 2025: "),run(0,"EK Emirates 233,925 (fifth-freedom Milan-JFK), DL Delta 112,181, AA American 99,086, UA United 90,767, NO Neos 69,061, B0 La Compagnie 38,676, N0 Norse 4,557. The single largest nonstop operator is Emirates on a fifth-freedom service; ITA serves New York from Rome, not Milan.")]),
  P([run(1,"Top connecting hubs, 2025: "),run(0,"Zurich 8,050, Copenhagen 7,040, Lisbon 6,297, Frankfurt 5,450, London 4,738, Paris 3,418.")]),
  P([run(1,"By point of origin (proxy for point of sale), 2025: "),run(0,"Italy-origin 417,561 (59%), US-origin 285,560 (40%).")]),

  H1("3. Genoa-NYC current routing"),
  note("Every Genoa-NYC passenger today is indirect; the table shows the top ten routings by hub and operating carrier, both directions, 2025."),
  table(["Connecting point / operator","2025","Share of GOA-NYC"],[
   ["Rome FCO / ITA","4,232","46%"],["Munich MUC / Lufthansa","1,888","20%"],["Amsterdam AMS / KLM","1,442","16%"],
   ["Amsterdam AMS / Delta","600","6%"],["Munich MUC / United","594","6%"],["Rome FCO / United","190","2%"],
   ["Rome FCO / Delta","116","1%"],["Rome FCO / American","60","<1%"],["Frankfurt FRA / Lufthansa","23","<1%"],
   ["London LHR / United","21","<1%"]],[5026,2000,2000]),
  P("By hub: Rome c.50%, Munich c.27%, Amsterdam c.22%. A direct Genoa service sells nonstop convenience against these established one-stop options, not against another nonstop."),

  H1("4. Seasonality"),
  note("Milan-NYC monthly O&D indexed to the average month (100), from the Sabre point-of-sale extract March 2025 to February 2026, both directions. Milan is the nearest large gateway and a sound proxy for the Genoa-NYC seasonal shape."),
  table(["Month","Passengers","Index (100 = avg)"],[
   ["January","43,769","69"],["February","46,575","73"],["March","55,232","87"],["April","74,500","117"],
   ["May","72,734","115"],["June","72,727","115"],["July","72,236","114"],["August","83,535","132"],
   ["September","69,187","109"],["October","64,363","101"],["November","49,342","78"],["December","57,158","90"]],
   [3626,2700,2700]),
  P("A leisure-weighted Atlantic profile: an August peak at 132, a broad April-September plateau circa 109-132, and a deep January-February trough circa 70, a peak-to-trough ratio of about 1.9. A 30-week summer GOA-NYC operation should be modelled against the plateau, not the annual mean, or its load factors and fares will read weaker than the operating reality."),

  H1("5. Cabin mix and yield"),
  note("Cabin split of Italy-NYC demand, 2025."),
  table(["Cabin","2025 passengers","Share"],[
   ["Economy (Discount Coach)","1,015,297","83%"],["Business","133,112","11%"],
   ["Premium economy (Premium Coach)","43,966","4%"],["First","23,610","2%"],
   brow(["Premium cabins combined","200,688","16.5%"])],[4626,2200,2200]),
  note("Premium-cabin share and yield, revenue per O&D passenger, by origin airport, 2025, Italy to NYC."),
  table(["Origin","Premium share","Yield (USD)"],[
   ["Milan MXP","19.6%","$928"],["Venice VCE","18.5%","$917"],["Naples NAP","14.1%","$918"],
   ["Milan LIN","17.1%","$744"],["Rome FCO","15.4%","$763"],["Bologna BLQ","12.1%","$690"],
   ["Genoa GOA","9.5%","$701"]],[3626,2700,2700]),
  P("Milan carries both the highest premium share and the highest yield; Genoa the lowest of each. This is what determines which operators would find a Genoa service attractive."),

  H1("6. Year-on-year movement by origin airport"),
  note("Change in O&D 2024 to 2025, both directions, against the Italian market as a whole."),
  table(["Origin airport","2024","2025","Change"],[
   ["Milan LIN","37,389","47,295","+26.5%"],["Genoa GOA","8,276","9,278","+12.1%"],["Bologna BLQ","47,511","53,061","+11.7%"],
   ["Naples NAP","156,579","151,275","-3.4%"],["Venice VCE","190,479","179,983","-5.5%"],
   ["Rome FCO","875,003","823,474","-5.9%"],["Milan MXP","754,649","708,445","-6.1%"],
   brow(["Italy, all airports","2,404,861","2,366,882","-1.6%"])],[3026,2000,2000,2000]),
  P("Genoa grew c.12% while the Italian market fell c.1.6% and the two largest gateways fell c.6%. Read against the estimate nature of 2025 and Genoa's small base, but the direction is the point."),

  H1("7. Catchment leakage: point-of-sale floor"),
  note("Where Milan-NYC tickets are sold, from the Sabre point-of-sale extract March 2025 to February 2026, both directions, 761,356 passengers. Point of sale records where the ticket was issued, not where the traveller lives."),
  table(["Point of sale","Passengers","Share"],[
   ["Italy","358,667","47%"],["United States","340,817","45%"],["Other / rest of world","61,872","8%"],
   brow(["Total Milan-NYC","761,356","100%"])],[4626,2200,2200]),
  note("Genoa 90-minute catchment identifiable within Italy-sold tickets."),
  table(["Genoa-catchment point of sale","Passengers"],[
   ["Genova","597"],["La Spezia","211"],["Alessandria","151"],["Recco","108"],["Tortona","108"],
   ["Santa Margherita","83"],["Imperia","80"],["Savona","67"],["Arenzano","57"],["Other catchment towns","45"],
   brow(["Genoa catchment, identifiable","1,507"])],[6026,3000]),
  P("Identifiable Genoa-catchment sales are 1,507, just 0.42% of Italy-sold Milan-NYC tickets and 0.20% of the whole market. Read this as a floor, not a catchment estimate. 26% of Italy-sold tickets carry no town at all, and the largest named buckets are Milan and Rome, because tickets are issued through agency, OTA and corporate desks concentrated in those cities, not where travellers live. Point of sale therefore collapses the catchment into the booking centres: it confirms leakage exists and sets a hard floor, but it cannot size it. Sizing the repatriable traffic needs the drive-time and cell catchment work in Stage 1."),

  H1("Three things worth knowing for Monday"),
  P("Genoa's New York demand rose c.12% to c.9,300 both ways while the Italian market fell c.1.6% and Rome and Milan fell c.6%, so Genoa is gaining share as the national gateways soften."),
  P("Milan Malpensa, the direct competitor 2.5 hours away, carries c.708,000 both ways at 92% nonstop, and its largest nonstop operator is Emirates on a fifth-freedom service, not a US or Italian carrier; ITA serves New York from Rome, not Milan."),
  P("Genoa is wholly indirect, routed c.50% over Rome, c.27% Munich and c.22% Amsterdam, so a direct service competes on nonstop convenience against one-stop incumbents."),
  P("Premium cabins are c.16% of the Italy-NYC market, with Milan the richest at c.$928 per passenger and Genoa the thinnest at c.9.5% and c.$701, which frames the cabin and operator question."),
  P("The prize is the catchment and leakage question, how much Genoa-area traffic now leaking to Milan and the hubs a direct service could repatriate. Point of sale confirms the leakage but cannot size it: only 0.2% of Milan-NYC tickets are identifiably Genoa-area, because tickets are issued in Milan and Rome, not where travellers live. Sizing the repatriable traffic needs the drive-time and cell catchment work in Stage 1.",{after:0}),
 ]}]
});
Packer.toBuffer(doc).then(b=>{fs.writeFileSync("/tmp/Genoa-NYC Sabre O&D pack.docx",b);console.log("written");});
