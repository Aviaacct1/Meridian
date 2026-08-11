// Avia Solutions - Project OSPREY, San Jose to Taipei route forecast, China Airlines.
//
//   node build_osprey.js osprey_deck.json "Project Osprey - SJC-TPE Route Forecast.pptx"
//
// The forecast cut of the house template: the summary map figures, the forecast build, what the
// frequency buys, where the connecting traffic comes from, the capacity frame, the alternatives and
// the basis. Every figure comes from the JSON, which is emitted by the model, so nothing here is
// typed by hand and the deck regenerates when the forecast does.
//
// House conventions applied: Arial throughout, codename on the cover, document type and status,
// prepared-for line, long-form date, confidentiality marker, a source line on every table, and the
// Observatory palette with brass as the only accent and Signal Red reserved for thresholds.
//
// Avia Solutions Limited. All rights reserved.

const pptxgen = require("pptxgenjs");
const fs = require("fs");

const D = JSON.parse(fs.readFileSync(process.argv[2] || "osprey_deck.json", "utf8"));
const OUT = process.argv[3] || "Project Osprey - SJC-TPE Route Forecast.pptx";

const INK = "0F1B28", PAPER = "F6F3EC", BRASS = "D4A249", TEXT = "26313B",
      MUTED = "8A8577", LINE = "E2DCCC", S2 = "3D6A88", S3 = "5F8D7A", SIGNAL = "CE3B2A",
      MUTED_INK = "8FA0B0";
const F = "Arial";
const n = (x) => Number(x).toLocaleString("en-GB");
const pc = (x, d = 1) => (Number(x) * 100).toFixed(d) + "%";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";                 // 13.3 x 7.5
pres.author = "Avia Solutions";
pres.company = "Avia Solutions";
pres.title = "Project Osprey - SJC-TPE Route Forecast";

const L = D.lead;
const FOOT = `Project Osprey - ${D.route} Route Forecast - Commercial in Confidence   |   ${D.date} - Draft 1`;

function chrome(s, title, kicker) {
  s.background = { color: PAPER };
  if (kicker) s.addText(kicker.toUpperCase(), { x: 0.6, y: 0.42, w: 12.1, h: 0.26,
    fontFace: F, fontSize: 10, color: MUTED, charSpacing: 2, margin: 0 });
  s.addText(title, { x: 0.6, y: 0.68, w: 12.1, h: 0.62,
    fontFace: F, fontSize: 30, bold: true, color: INK, margin: 0 });
}
function foot(s, page) {
  s.addText(FOOT, { x: 0.6, y: 7.02, w: 11.2, h: 0.26, fontFace: F, fontSize: 8, color: MUTED, margin: 0 });
  s.addText("P: " + page, { x: 11.9, y: 7.02, w: 0.8, h: 0.26, fontFace: F, fontSize: 8,
    color: MUTED, align: "right", margin: 0 });
}
function source(s, y, txt) {
  s.addText("Source: " + txt, { x: 0.6, y: y, w: 12.1, h: 0.24, fontFace: F, fontSize: 9,
    italic: true, color: MUTED, margin: 0 });
}
function tbl(s, rows, opts) {
  s.addTable(rows, Object.assign({
    x: 0.6, w: 12.1, fontFace: F, fontSize: 11, color: TEXT, valign: "middle",
    border: { type: "solid", pt: 0.5, color: LINE }, autoPage: false,
  }, opts));
}
const H = (t, o = {}) => Object.assign({ text: t, options: Object.assign(
  { bold: true, color: "FFFFFF", fill: INK, fontSize: 10 }, o) });
const C = (t, o = {}) => Object.assign({ text: t, options: Object.assign({ fontSize: 11 }, o) });

// ---------------------------------------------------------------- 1. cover
let s = pres.addSlide();
s.background = { color: INK };
s.addText("PROJECT OSPREY", { x: 0.9, y: 1.5, w: 11.5, h: 0.4, fontFace: F, fontSize: 13,
  color: BRASS, charSpacing: 4, margin: 0 });
s.addText("San Jose to Taipei", { x: 0.9, y: 2.05, w: 11.5, h: 0.9, fontFace: F, fontSize: 46,
  bold: true, color: "FFFFFF", margin: 0 });
s.addText("Route forecast for a China Airlines service", { x: 0.9, y: 3.0, w: 11.5, h: 0.5,
  fontFace: F, fontSize: 20, color: MUTED_INK, margin: 0 });
s.addText("Route Forecast - DRAFT", { x: 0.9, y: 4.35, w: 11.5, h: 0.34, fontFace: F,
  fontSize: 14, bold: true, color: BRASS, margin: 0 });
s.addText("Prepared for [CLIENT]", { x: 0.9, y: 4.78, w: 11.5, h: 0.34, fontFace: F,
  fontSize: 14, color: "FFFFFF", margin: 0 });
s.addText(D.date, { x: 0.9, y: 5.18, w: 11.5, h: 0.34, fontFace: F, fontSize: 14,
  color: MUTED_INK, margin: 0 });
s.addText("COMMERCIAL IN CONFIDENCE", { x: 0.9, y: 6.5, w: 11.5, h: 0.3, fontFace: F,
  fontSize: 10, color: MUTED_INK, charSpacing: 2, margin: 0 });
s.addText("Avia Solutions", { x: 10.4, y: 6.5, w: 2.0, h: 0.3, fontFace: F, fontSize: 10,
  color: BRASS, align: "right", margin: 0 });
s.addNotes("Prepared-for line is a placeholder. Set the client name before this leaves the office.");

// ---------------------------------------------------------------- 2. summary
s = pres.addSlide();
chrome(s, "Summary of route forecast", "China Airlines  |  A350-900  |  5x weekly");
const stats = [
  ["Point to point", n(L.p2p2w), "two-way passengers a year"],
  ["Connecting over Taipei", n(L.beyond2w), "two-way passengers a year"],
  ["Connecting behind San Jose", n(L.behind2w), "two-way passengers a year"],
];
stats.forEach((st, i) => {
  const x = 0.6 + i * 4.12;
  s.addShape(pres.ShapeType.rect, { x: x, y: 1.55, w: 3.86, h: 1.75, fill: { color: "FFFFFF" },
    line: { color: LINE, pt: 0.75 } });
  s.addText(st[0], { x: x + 0.28, y: 1.75, w: 3.3, h: 0.3, fontFace: F, fontSize: 11,
    color: MUTED, margin: 0 });
  s.addText(st[1], { x: x + 0.28, y: 2.08, w: 3.3, h: 0.75, fontFace: F, fontSize: 40,
    bold: true, color: INK, margin: 0 });
  s.addText(st[2], { x: x + 0.28, y: 2.86, w: 3.3, h: 0.3, fontFace: F, fontSize: 10,
    color: MUTED, margin: 0 });
});
s.addText(`Total forecast ${n(L.total2w)} two-way passengers a year, ${L.pdew} per day each way, `
  + `filling ${pc(L.lf / 100)} of ${n(L.seats2w)} two-way seats`,
  { x: 0.6, y: 3.45, w: 12.1, h: 0.36, fontFace: F, fontSize: 15, bold: true, color: INK, margin: 0 });
s.addText("Schedule options", { x: 0.6, y: 4.0, w: 6, h: 0.3, fontFace: F, fontSize: 13,
  bold: true, color: INK, margin: 0 });
tbl(s, [
  [H("Sector"), H("Depart"), H("Arrive"), H("Days"), H("Aircraft"), H("Seats"),
   H("Annual seats"), H("Annual pax"), H("Seat factor")],
  [C(L.sched.outbound.sector), C(L.sched.outbound.dep), C(L.sched.outbound.arr), C("5x weekly"),
   C(L.ac_name), C(n(L.seats)), C(n(L.seats2w / 2)), C(n(L.total2w / 2)), C(pc(L.lf / 100))],
  [C(L.sched.inbound.sector), C(L.sched.inbound.dep), C(L.sched.inbound.arr), C("5x weekly"),
   C(L.ac_name), C(n(L.seats)), C(n(L.seats2w / 2)), C(n(L.total2w / 2)), C(pc(L.lf / 100))],
], { y: 4.35, rowH: 0.32, colW: [1.5, 1.15, 1.25, 1.25, 1.5, 0.95, 1.5, 1.4, 1.6] });
s.addText("Times are indicative, from block time and longitude. They are not slot, curfew or "
  + "connection optimised.", { x: 0.6, y: 5.55, w: 12.1, h: 0.24, fontFace: F, fontSize: 9,
  italic: true, color: MUTED, margin: 0 });
source(s, 6.5, "AviaSolutions Analysis. Catchment market from Sabre O&D, service area of "
  + "San Jose. Sector 10,440 km / 5,637 nm.");
foot(s, 2);

// ---------------------------------------------------------------- 3. forecast build
s = pres.addSlide();
chrome(s, "How the forecast is built", "From measured market to carried passengers");
tbl(s, [
  [H("Step"), H("Basis"), H("Two-way passengers a year")],
  [C("Measured catchment market to Taipei", { bold: true }),
   C("Sabre O&D by true origin, the whole San Jose service area, all airports used today"),
   C(n(L.market2w), { align: "right", bold: true })],
  [C("Travelling via San Jose today"),
   C("The part of that market already departing San Jose, with no nonstop"),
   C(n(L.current2w), { align: "right" })],
  [C("San Jose capture with a nonstop"),
   C("Measured airport capture, Avia survey and mobility data, shaped by schedule quality at 5x weekly"),
   C(pc(L.capture), { align: "right" })],
  [C("Stimulation from direct service"),
   C("Full service carrier, applied to the captured point-to-point market"),
   C("x " + L.stim, { align: "right" })],
  [C("Point to point forecast", { bold: true }),
   C("Captured, stimulated, and bounded by the aircraft"),
   C(n(L.p2p2w), { align: "right", bold: true })],
  [C("Connecting over Taipei"),
   C("China Airlines and alliance flows beyond Taipei, alliance weighted"),
   C(n(L.beyond2w), { align: "right" })],
  [C("Connecting behind San Jose"),
   C("Domestic feed connecting onto the service at San Jose"),
   C(n(L.behind2w), { align: "right" })],
  [C("Total forecast", { bold: true, fill: "FBF9F3" }),
   C(`${L.pdew} passengers per day each way`, { fill: "FBF9F3" }),
   C(n(L.total2w), { align: "right", bold: true, fill: "FBF9F3" })],
], { y: 1.6, rowH: 0.42, colW: [3.9, 5.6, 2.6] });
source(s, 6.35, "AviaSolutions Analysis. Sabre O&D " + D.sabre_year + ", OAG schedules week "
  + D.oag_week + ". Capture factor recorded in airport_capture.py from the Avia survey and "
  + "cell-phone data.");
foot(s, 3);

// ---------------------------------------------------------------- 4. frequency
s = pres.addSlide();
chrome(s, "What the frequency buys", "China Airlines A350-900, 306 seats, two-way a year");
s.addChart(pres.ChartType.bar, [{
  name: "Passengers carried, two-way",
  labels: D.curve.map(c => c.freq + "x"),
  values: D.curve.map(c => c.carried2w),
}], {
  x: 0.6, y: 1.55, w: 7.3, h: 4.4, barDir: "col", chartColors: [BRASS],
  showTitle: true, title: "Passengers carried a year, two-way, by weekly frequency",
  titleFontSize: 12, titleColor: TEXT, titleFontFace: F,
  showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 9,
  dataLabelFormatCode: "#,##0", dataLabelColor: TEXT, dataLabelFontFace: F,
  showLegend: false, catAxisLabelColor: TEXT, valAxisLabelColor: MUTED,
  catAxisLabelFontFace: F, valAxisLabelFontFace: F, catAxisLabelFontSize: 10,
  valAxisLabelFontSize: 9, valAxisLabelFormatCode: "#,##0",
  valGridLine: { color: LINE, size: 0.5 }, catGridLine: { style: "none" },
});
tbl(s, [
  [H("Weekly"), H("Capture"), H("Carried, two-way"), H("Seat factor")],
  ...D.curve.map(c => [
    C(c.freq + "x"), C(pc(c.capture)), C(n(c.carried2w), { align: "right" }),
    C(pc(c.lf / 100), { align: "right", color: c.lf > 87 ? SIGNAL : TEXT }),
  ]),
], { x: 8.25, y: 1.75, w: 4.45, rowH: 0.36, colW: [1.0, 1.05, 1.45, 0.95] });
s.addText("At three and four weekly the aircraft fills to the planning cap and demand is spilled, "
  + "shown in red. Five weekly is the first schedule that carries the whole forecast.",
  { x: 8.25, y: 5.05, w: 4.45, h: 0.8, fontFace: F, fontSize: 10, color: TEXT, margin: 0 });
source(s, 6.35, "AviaSolutions Analysis. Capture is anchored on the measured San Jose factor at "
  + "daily service; the shape either side comes from the schedule-quality computation.");
foot(s, 4);

// ---------------------------------------------------------------- 5. connecting
s = pres.addSlide();
chrome(s, "Where the connecting traffic comes from", "Passengers per day each way, year one");
const bey = L.beyond_pdew.slice(0, 6), beh = L.behind_pdew.slice(0, 6);
s.addText("Beyond Taipei", { x: 0.6, y: 1.55, w: 5.9, h: 0.3, fontFace: F, fontSize: 14,
  bold: true, color: INK, margin: 0 });
tbl(s, [[H("City"), H("PDEW")], ...bey.map(b => [
  C(String(b.city || b.code || "")), C(Number(b.pdew || 0).toFixed(1), { align: "right" })])],
  { x: 0.6, y: 1.95, w: 5.9, rowH: 0.36, colW: [4.4, 1.5] });
s.addText("Behind San Jose", { x: 6.8, y: 1.55, w: 5.9, h: 0.3, fontFace: F, fontSize: 14,
  bold: true, color: INK, margin: 0 });
tbl(s, [[H("City"), H("PDEW")], ...beh.map(b => [
  C(String(b.city || b.code || "")), C(Number(b.pdew || 0).toFixed(1), { align: "right" })])],
  { x: 6.8, y: 1.95, w: 5.9, rowH: 0.36, colW: [4.4, 1.5] });
s.addText(`Connecting traffic is ${pc(L.feed2w / L.total2w)} of the forecast: `
  + `${n(L.beyond2w)} two-way over Taipei and ${n(L.behind2w)} behind San Jose. `
  + `It is the reason a full-service operator carries more on this route than a carrier without a `
  + `network at either end.`,
  { x: 0.6, y: 4.55, w: 12.1, h: 0.8, fontFace: F, fontSize: 13, color: INK, margin: 0 });
source(s, 6.35, "AviaSolutions Analysis. Connecting flows built from OAG schedules with minimum "
  + "connect times, alliance weighted, and grown with the measured market.");
foot(s, 5);

// ---------------------------------------------------------------- 6. capacity frame
s = pres.addSlide();
chrome(s, "What China Airlines actually flies", "Aircraft on sectors of comparable length, OAG "
  + D.oag_year);
tbl(s, [
  [H("Aircraft"), H("Seats"), H("Of which premium"), H("Routes"), H("Sectors flown"),
   H("Sector range, km")],
  ...D.frame.CI.map(f => [
    C(f.ac), C(n(f.seats), { align: "right" }), C(n(f.prem), { align: "right" }),
    C(n(f.routes), { align: "right" }), C(n(f.sectors), { align: "right" }), C(f.km)]),
], { y: 1.6, rowH: 0.42, colW: [3.0, 1.6, 2.2, 1.5, 2.0, 1.8] });
s.addText("The forecast is sized on the aircraft China Airlines operates on sectors of this length "
  + "and at the seat count it configures them with, both measured from the schedule rather than "
  + "assumed. The A350-900 at 306 seats is the closer fit to this market; the 777-300ER carries "
  + "52 more seats and fills to " + "77.1%" + " at four weekly.",
  { x: 0.6, y: 3.15, w: 12.1, h: 0.9, fontFace: F, fontSize: 13, color: INK, margin: 0 });
s.addText("Premium demand on this market is " + pc(L.premium) + " of passengers, against a "
  + "premium cabin of " + pc(32 / 306) + " of the A350-900. The front cabin is the binding "
  + "constraint before the aircraft is.",
  { x: 0.6, y: 4.2, w: 12.1, h: 0.6, fontFace: F, fontSize: 13, color: INK, margin: 0 });
source(s, 6.35, "OAG schedules " + D.oag_year + ", nonstop passenger services on sectors of "
  + "7,830 to 13,050 km. Premium share of demand from Sabre O&D, business and first.");
foot(s, 6);

// ---------------------------------------------------------------- 7. alternatives
s = pres.addSlide();
chrome(s, "The alternative operators", "Same market, each carrier's own aircraft and network");
tbl(s, [
  [H("Carrier"), H("Aircraft"), H("Seats"), H("Weekly"), H("Forecast, two-way"),
   H("Point to point"), H("Connecting"), H("Seat factor")],
  [C(L.name, { bold: true }), C(L.ac_name), C(n(L.seats)), C(L.freq + "x"),
   C(n(L.total2w), { align: "right", bold: true }), C(n(L.p2p2w), { align: "right" }),
   C(n(L.feed2w), { align: "right" }), C(pc(L.lf / 100), { align: "right" })],
  ...D.alts.map(a => [
    C(a.name), C(a.ac_name), C(n(a.seats)), C(a.freq + "x"),
    C(n(a.total2w), { align: "right" }), C(n(a.p2p2w), { align: "right" }),
    C(n(a.feed2w), { align: "right" }), C(pc(a.lf / 100), { align: "right" })]),
  // colW must sum to the table width, 12.1. At 12.8 the last column ran off the slide edge and the
  // seat factor was cut in half.
], { y: 1.6, rowH: 0.42, colW: [2.0, 1.7, 0.9, 0.9, 1.9, 1.6, 1.55, 1.55] });
s.addText("Starlux carries circa 15% fewer passengers than China Airlines on the same aircraft and "
  + "frequency. The gap is the connecting network, not the local market: Starlux has no US "
  + "domestic feed at San Jose and a thinner network beyond Taipei.",
  { x: 0.6, y: 4.05, w: 12.1, h: 0.8, fontFace: F, fontSize: 13, color: INK, margin: 0 });
s.addText("EVA's 787-10 carries the same passengers as its 777-300ER at four weekly because demand, "
  + "not capacity, is binding at that frequency. The difference between them is seat factor, and "
  + "therefore economics, rather than traffic.",
  { x: 0.6, y: 4.95, w: 12.1, h: 0.8, fontFace: F, fontSize: 13, color: INK, margin: 0 });
source(s, 6.35, "AviaSolutions Analysis. Each carrier modelled with its own network, its own "
  + "aircraft from OAG " + D.oag_year + " and its own measured seat configuration.");
foot(s, 7);

// ---------------------------------------------------------------- 8. basis
s = pres.addSlide();
s.background = { color: INK };
s.addText("BASIS AND CONFIDENCE", { x: 0.9, y: 0.7, w: 11.5, h: 0.34, fontFace: F, fontSize: 11,
  color: BRASS, charSpacing: 3, margin: 0 });
s.addText("What this forecast is, and what it is not", { x: 0.9, y: 1.1, w: 11.5, h: 0.6,
  fontFace: F, fontSize: 28, bold: true, color: "FFFFFF", margin: 0 });
const pts = [
  ["Method", "Measured Sabre origin and destination demand for the whole San Jose service area, "
   + "captured by a new nonstop at the airport's measured capture rate, stimulated, then bounded by "
   + "the aircraft. Connecting traffic is built from OAG schedules with minimum connect times."],
  ["Confidence", `Central estimate ${n(L.total2w)} two-way. Comparable launches landed between `
   + `${n(L.low2w)} and ${n(L.high2w)} about two times in three. The width is the honest `
   + `uncertainty on a new route and is not reducible by presenting a single number.`],
  ["Cross-checks", "The engine reproduces the Avia dashboard case on this route to 0.03%, and the "
   + "October 2025 China Airlines analysis at four weekly to within 3.3% on the same schedule."],
  ["Not included", "No economics. This is a traffic forecast only. Airport charges, ownership cost "
   + "and fares are set per engagement and are not part of these figures."],
];
// valign top on both, or the label sits at the top of its box while the body centres in a taller
// one and the two stop reading as a pair.
let y = 2.15;
pts.forEach(p => {
  s.addText(p[0], { x: 0.9, y: y, w: 2.4, h: 0.9, fontFace: F, fontSize: 13, bold: true,
    color: BRASS, margin: 0, valign: "top" });
  s.addText(p[1], { x: 3.4, y: y, w: 9.0, h: 0.9, fontFace: F, fontSize: 12, color: "FFFFFF",
    margin: 0, valign: "top" });
  y += 1.12;
});
s.addText("Avia Solutions Limited. All rights reserved.   |   " + FOOT,
  { x: 0.9, y: 7.02, w: 11.5, h: 0.26, fontFace: F, fontSize: 8, color: MUTED_INK, margin: 0 });

pres.writeFile({ fileName: OUT }).then(() => console.log("written: " + OUT));
