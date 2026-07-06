// Avia Solutions - Genoa to New York route business case deck (generalisation test)
// House style: UK English, no em/en dashes, "circa". Italy in euros, US in dollars.
const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Avia Solutions";
pres.company = "Avia Solutions";
pres.title = "Genoa to New York - Route Business Case";
pres.subject = "Genoa GOA-New York route forecast and business case";

const NAVY = "13243B", NAVY2 = "1E3A5F", GOLD = "C8A45C", SLATE = "2B2B2B", MUTED = "6B7A8D";
const LIGHT = "F4F6F8", PANEL = "EAEEF2", WHITE = "FFFFFF", BLUE = "3E6CA6", TEAL = "2E8E94";
const HEAD = "Cambria", BODY = "Calibri";
const W = 13.333, H = 7.5, MX = 0.7;
let pageNo = 0;

function footer(s, section) {
  pageNo++;
  s.addText([{ text: "Avia Solutions", options: { color: MUTED, bold: true } },
     { text: "   Genoa - New York  |  Airbus A321XLR", options: { color: MUTED } }],
    { x: MX, y: H - 0.42, w: 9.5, h: 0.3, fontSize: 8.5, fontFace: BODY, margin: 0, valign: "middle" });
  s.addText(String(pageNo), { x: W - 1.0, y: H - 0.42, w: 0.5, h: 0.3, fontSize: 9, fontFace: BODY, color: MUTED, align: "right", valign: "middle", margin: 0 });
  if (section) s.addText(section.toUpperCase(), { x: W - 4.6, y: H - 0.42, w: 3.3, h: 0.3, fontSize: 8, fontFace: BODY, color: MUTED, align: "right", valign: "middle", charSpacing: 1, margin: 0 });
}
function title(s, text, sub) {
  s.addText(text, { x: MX, y: 0.45, w: W - 2*MX, h: 0.7, fontSize: 27, fontFace: HEAD, color: NAVY, bold: true, margin: 0, valign: "middle" });
  if (sub) s.addText(sub, { x: MX, y: 1.18, w: W - 2*MX, h: 0.4, fontSize: 13, fontFace: BODY, color: GOLD, italic: true, margin: 0, valign: "middle" });
}
function sourceLine(s, text, y) {
  s.addText("Sources: " + text, { x: MX, y: y || (H - 0.78), w: W - 2*MX, h: 0.33, fontSize: 8, fontFace: BODY, color: MUTED, italic: true, margin: 0, valign: "middle" });
}
function shadow() { return { type: "outer", color: "000000", blur: 7, offset: 2, angle: 90, opacity: 0.12 }; }
function statCard(s, x, y, w, h, value, label, sub, accent) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: WHITE }, line: { color: PANEL, width: 1 }, rectRadius: 0.06, shadow: shadow() });
  s.addText(value, { x: x+0.18, y: y+0.16, w: w-0.36, h: h*0.45, fontSize: 30, fontFace: HEAD, color: accent || NAVY, bold: true, margin: 0, valign: "middle", align: "left", autoFit: true });
  s.addText(label, { x: x+0.2, y: y+h*0.52, w: w-0.4, h: h*0.24, fontSize: 11.5, fontFace: BODY, color: SLATE, bold: true, margin: 0, valign: "top" });
  if (sub) s.addText(sub, { x: x+0.2, y: y+h*0.72, w: w-0.4, h: h*0.26, fontSize: 9.5, fontFace: BODY, color: MUTED, margin: 0, valign: "top" });
}
function photoSlot(s, x, y, w, h, label) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: PANEL }, line: { color: MUTED, width: 1, dashType: "dash" }, rectRadius: 0.05 });
  s.addText([
    { text: "IMAGE SLOT", options: { bold: true, color: NAVY2, fontSize: 11, breakLine: true, charSpacing: 1 } },
    { text: label, options: { color: MUTED, fontSize: 10, breakLine: true } },
    { text: "Airport to supply", options: { color: MUTED, fontSize: 8.5, italic: true } },
  ], { x: x+0.1, y, w: w-0.2, h, align: "center", valign: "middle", fontFace: BODY, margin: 0 });
}
function bullets(s, x, y, w, h, items, fontSize) {
  s.addText(items.map(t => ({ text: t, options: { bullet: { code: "2022", indent: 14 }, color: SLATE, breakLine: true, paraSpaceAfter: 8 } })),
    { x, y, w, h, fontSize: fontSize || 13, fontFace: BODY, valign: "top", margin: 0 });
}
function sectionDivider(num, name, photoLabel) {
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addText(num, { x: MX, y: 2.0, w: 3, h: 1.4, fontSize: 72, fontFace: HEAD, color: GOLD, bold: true, margin: 0 });
  s.addText(name, { x: MX, y: 3.45, w: 7.4, h: 1.6, fontSize: 34, fontFace: HEAD, color: WHITE, bold: true, margin: 0, valign: "top" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.5, y: 1.4, w: 4.1, h: 4.7, fill: { color: NAVY2 }, line: { color: GOLD, width: 1, dashType: "dash" }, rectRadius: 0.05 });
  s.addText([
    { text: "IMAGE SLOT", options: { bold: true, color: GOLD, fontSize: 12, breakLine: true, charSpacing: 1 } },
    { text: photoLabel, options: { color: "C9D4E0", fontSize: 11, breakLine: true } },
    { text: "Airport to supply", options: { color: MUTED, fontSize: 9, italic: true } },
  ], { x: 8.6, y: 1.4, w: 3.9, h: 4.7, align: "center", valign: "middle", fontFace: BODY, margin: 0 });
  pageNo++;
  s.addText(String(pageNo), { x: W - 1.0, y: H - 0.42, w: 0.5, h: 0.3, fontSize: 9, fontFace: BODY, color: "8FA0B3", align: "right", margin: 0 });
}

// ===== 1 COVER
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: W, h: 2.7, fill: { color: NAVY2 } });
  s.addText([{ text: "IMAGE SLOT   ", options: { bold: true, color: GOLD, fontSize: 11, charSpacing: 1 } },
    { text: "Genoa / Italian Riviera hero image (airport to supply)", options: { color: "AEBCCB", fontSize: 11, italic: true } }],
    { x: MX, y: 0.2, w: 11, h: 0.4, valign: "middle", fontFace: BODY, margin: 0 });
  s.addText("Genoa to New York\nA transatlantic opportunity", { x: MX, y: 3.0, w: 11.5, h: 1.6, fontSize: 40, fontFace: HEAD, color: WHITE, bold: true, margin: 0, lineSpacingMultiple: 1.0 });
  s.addText("Aeroporto di Genova Cristoforo Colombo   |   Genoa - New York   |   Airbus A321XLR", { x: MX, y: 4.85, w: 11.8, h: 0.5, fontSize: 16, fontFace: BODY, color: GOLD, margin: 0 });
  s.addText([{ text: "Route forecast and business case", options: { color: "C9D4E0", fontSize: 13, breakLine: true } },
    { text: "Prepared by Avia Solutions  |  June 2026", options: { color: MUTED, fontSize: 12 } }],
    { x: MX, y: 5.7, w: 8, h: 0.8, fontFace: BODY, margin: 0, valign: "top" });
  s.addText("[ Airport logo ]      [ Avia Solutions logo ]      [ Airline logo ]", { x: MX, y: 6.7, w: 11, h: 0.4, fontSize: 10, fontFace: BODY, color: MUTED, italic: true, margin: 0 });
}

// ===== 2 CONTENTS
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  title(s, "Contents");
  const items = [
    ["01", "Why New York from Genoa", "The largest Italian-American market on earth, a record tourism region, and a major cruise homeport"],
    ["02", "The forecast", "The Liguria catchment, the leakage to Milan, and the demand a Genoa nonstop recaptures"],
    ["03", "The case and the precedent", "The A321XLR, United's secondary-city template, seasonality, and Genoa airport"],
  ];
  let y = 2.0;
  items.forEach(([n, t, d]) => {
    s.addText(n, { x: MX, y, w: 0.9, h: 0.8, fontSize: 26, fontFace: HEAD, color: GOLD, bold: true, margin: 0, valign: "top" });
    s.addText(t, { x: MX+1.0, y, w: 10.6, h: 0.4, fontSize: 17, fontFace: HEAD, color: NAVY, bold: true, margin: 0, valign: "top" });
    s.addText(d, { x: MX+1.0, y: y+0.42, w: 11.0, h: 0.5, fontSize: 11.5, fontFace: BODY, color: MUTED, margin: 0, valign: "top" });
    y += 1.25;
  });
  footer(s, "Contents");
}

// ===== 3 OPPORTUNITY AT A GLANCE
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  title(s, "The opportunity", "A New York nonstop for Liguria, on a long-range narrowbody");
  statCard(s, MX, 1.85, 3.7, 1.75, "553,300", "New York O&D market", "Annual demand from the Genoa catchment", NAVY);
  statCard(s, MX+3.95, 1.85, 3.7, 1.75, "circa 92,500", "addressable for a nonstop", "Demand a Genoa service can serve", BLUE);
  statCard(s, MX+7.9, 1.85, 3.7, 1.75, "circa 0%", "captured at Genoa today", "Almost all leaks to Milan and Rome", GOLD);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y: 3.95, w: 7.4, h: 2.5, fill: { color: LIGHT }, line: { color: PANEL, width: 1 }, rectRadius: 0.05 });
  s.addText("Proposed service", { x: MX+0.25, y: 4.1, w: 7, h: 0.4, fontSize: 14, fontFace: HEAD, color: NAVY, bold: true, margin: 0 });
  s.addTable([
    [{ text: "Aircraft", options: { bold: true } }, "Airbus A321XLR, circa 182 seats (162 economy, 20 business)"],
    [{ text: "Range", options: { bold: true } }, "Genoa - New York circa 3,750nm, well inside the type's 4,700nm"],
    [{ text: "Natural operator", options: { bold: true } }, "A Newark-hubbed XLR carrier (United fits the pattern)"],
    [{ text: "Profile", options: { bold: true } }, "Leisure and visiting-friends led, with a business layer"],
  ], { x: MX+0.25, y: 4.55, w: 6.9, h: 1.8, fontSize: 11, fontFace: BODY, color: SLATE, border: { type: "solid", pt: 0.5, color: PANEL }, colW: [1.9, 5.0], valign: "middle", rowH: 0.4 });
  photoSlot(s, MX+7.7, 3.95, 3.9, 2.5, "Map: Genoa - New York great circle");
  sourceLine(s, "Avia QSI catchment and demand model (Sabre O&D), to be refreshed on the live base. Figures illustrative.");
  footer(s, "Summary");
}

// ===== SECTION 01
sectionDivider("01", "Why New York\nfrom Genoa", "Genoa old port / Italian Riviera");

// ---- diaspora
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  title(s, "The largest Italian-American market on earth", "A deep, year-round visiting-friends-and-relatives base");
  statCard(s, MX, 1.85, 3.55, 1.7, "circa 2.6m", "Italians in NY metro", "The largest of any US metro", NAVY);
  statCard(s, MX+3.75, 1.85, 3.55, 1.7, "circa 6.3m", "in the US northeast", "39% of all US Italian-Americans", BLUE);
  statCard(s, MX+7.5, 1.85, 3.55, 1.7, "23.5%", "of US arrivals to Italy", "Come from New York airports alone", TEAL);
  bullets(s, MX, 3.95, 11.9, 1.9, [
    "The New York region holds the densest Italian-American population anywhere outside Italy. The wider northeast (New York, New Jersey, Connecticut, Massachusetts, Pennsylvania, Rhode Island) accounts for circa 39% of all US Italian-Americans.",
    "This is a resilient, year-round visiting-friends-and-relatives base that is less seasonal and less price-sensitive than pure leisure, and it anchors a US-Italy route at New York specifically.",
    "Genoa carries a direct cultural hook: the city is the birthplace of Christopher Columbus, the airport's namesake and the figure at the centre of New York's Italian-American identity.",
  ], 12.5);
  sourceLine(s, "US Census Bureau ACS 2024 (B04006); ENIT / ForwardKeys (Mar 2026). NY metro figure circa 2021 base, to refresh from data.census.gov.");
  footer(s, "Why New York");
}

// ---- tourism region
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  title(s, "A record, growing tourism region", "Liguria and the Italian Riviera, led by foreign demand");
  statCard(s, MX, 1.85, 3.55, 1.7, "16.2m", "Liguria arrivals, 2024", "An all-time record, foreign-led growth", NAVY);
  statCard(s, MX+3.75, 1.85, 3.55, 1.7, "Top 10", "global UNESCO site", "Cinque Terre, circa one hour from Genoa", BLUE);
  statCard(s, MX+7.5, 1.85, 3.55, 1.7, "Best in Travel", "Genoa, Lonely Planet 2025", "The only Italian city named", GOLD);
  bullets(s, MX, 3.95, 11.9, 1.9, [
    "Liguria set a tourism record in 2024, with all the growth coming from foreign visitors. Genoa city arrivals reached 4.6m, with foreign arrivals up 5.5%.",
    "The region packs world-class draws within an hour of the airport: the Cinque Terre, Portofino, the Riviera and a UNESCO-listed historic centre.",
    "Genoa's selection as Lonely Planet's only Italian Best in Travel city for 2025 gives the destination fresh, marketable visibility in the US.",
  ], 12.5);
  sourceLine(s, "Regione Liguria Tourism Observatory (Feb 2025); Citta della Spezia (Apr 2026); Lonely Planet Best in Travel 2025.");
  footer(s, "Why New York");
}

// ---- premium US-Italy leisure market
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  title(s, "The premium US to Italy leisure market", "High-spend, long-stay, and growing fast");
  statCard(s, MX, 1.85, 3.55, 1.7, "circa 4.1m", "US travellers to Italy", "Spending over EUR 6.6bn in 2025", NAVY);
  statCard(s, MX+3.75, 1.85, 3.55, 1.7, "+22%", "US arrivals, to Aug 2025", "Among the fastest-growing US markets", BLUE);
  statCard(s, MX+7.5, 1.85, 3.55, 1.7, "EUR 191", "US spend per night", "The highest of any nationality", TEAL);
  bullets(s, MX, 3.95, 11.9, 1.9, [
    "The United States is Italy's premium inbound market: the highest per-night spend of any nationality, long stays of 8 to 10 nights, and a profile that is 88% leisure.",
    "US traffic to Southern Europe is running circa 27% above 2019, against roughly flat growth Europe-wide. Italy is one of the strongest US-Europe markets.",
    "This high-yield, long-stay leisure profile supports a premium cabin and strong ancillary revenue on a Genoa service.",
  ], 12.5);
  sourceLine(s, "ENIT on Bank of Italy data (Mar 2026); Bank of Italy Survey on International Tourism 2024; OAG (2024); Italian Ministry of Tourism (Oct 2025).");
  footer(s, "Why New York");
}

// ---- cruise homeport
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  title(s, "A major cruise homeport", "Air-relevant embarkation demand on top of the leisure base");
  bullets(s, MX, 1.95, 7.2, 3.5, [
    "Genoa is the seventh-largest cruise port in the Mediterranean, handling circa 1.6m cruise passengers in 2025.",
    "Of these, circa 620,000 are homeport (embarking or disembarking) passengers who must travel to or from Genoa, many by air.",
    "Genoa is the home of Costa Cruises and an MSC base. MSC already sells flight-inclusive packages with a guest lounge at Genoa airport.",
    "The United States is the world's largest cruise source market, so a New York nonstop strengthens Genoa as a transatlantic embarkation port.",
  ], 12);
  statCard(s, MX+7.5, 1.95, 4.1, 1.75, "circa 620,000", "air-relevant cruise pax", "Homeport passengers at Genoa, 2025", NAVY);
  photoSlot(s, MX+7.5, 3.9, 4.1, 1.75, "Genoa cruise terminal / MSC or Costa ship");
  sourceLine(s, "Risposte Turismo / Seatrade Cruise (Mar 2026); Ports of Genoa; MSC Cruises. Fly-cruise air share to be confirmed from cruise-line data.");
  footer(s, "Why New York");
}

// ===== SECTION 02
sectionDivider("02", "The forecast", "Liguria map / drive-time to Milan");

// ---- catchment and the leak to Milan
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  title(s, "The catchment, and the leak to Milan", "Genoa's New York demand drives two hours to Malpensa today");
  bullets(s, MX, 1.95, 7.2, 3.5, [
    "The Genoa catchment generates circa 553,300 two-way passengers a year to New York, but almost none of it flies from Genoa.",
    "With no nonstop, Liguria passengers drive circa two hours to Milan Malpensa, or connect over Rome, Munich or Amsterdam.",
    "Milan Malpensa runs circa four daily New York nonstops (Delta, American, Emirates and Neos). That is the pool a Genoa service would partly recapture.",
    "Recapturing local demand onto a local nonstop is the core of the case, the same logic that built United's secondary-Italy routes.",
  ], 12);
  statCard(s, MX+7.5, 1.95, 4.1, 1.75, "circa 198 km", "Genoa to Malpensa", "Roughly a two-hour drive each way", NAVY);
  statCard(s, MX+7.5, 3.9, 4.1, 1.75, "circa 4 daily", "Milan - New York nonstops", "The leakage a Genoa service recaptures", BLUE);
  sourceLine(s, "Avia QSI catchment model; Rome2Rio; OAG / schedule data (Milan-New York frequencies to be confirmed against OAG).");
  footer(s, "The forecast");
}

// ---- forecast / repatriation
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  title(s, "Recapturing the leakage: the forecast", "What a daily A321XLR can carry");
  const hdr = ["Demand layer", "Passengers (each way)", "Note"].map(t => ({ text: t, options: { bold: true, color: WHITE, fill: { color: NAVY }, align: t === "Demand layer" ? "left" : (t === "Note" ? "left" : "right"), fontSize: 11.5 } }));
  const rows = [hdr,
    ["Natural catchment demand to New York", "circa 92,500", "Genoa's own addressable market"].map((c, j) => ({ text: c, options: { fill: { color: WHITE }, color: SLATE, align: j === 1 ? "right" : "left", fontSize: 12 } })),
    ["Captured at Genoa today", "circa 7,000", "Almost all leaks to Milan"].map((c, j) => ({ text: c, options: { fill: { color: LIGHT }, color: SLATE, align: j === 1 ? "right" : "left", fontSize: 12 } })),
    ["Leaked pool a nonstop can win", "circa 85,500", "Demand driving past Genoa today"].map((c, j) => ({ text: c, options: { fill: { color: WHITE }, color: SLATE, align: j === 1 ? "right" : "left", fontSize: 12 } })),
    ["Repatriated at 65% capture", "circa 55,600", "Bounded, conservative capture"].map((c, j) => ({ text: c, options: { fill: { color: LIGHT }, color: SLATE, align: j === 1 ? "right" : "left", fontSize: 12 } })),
    ["Genoa nonstop forecast", "circa 62,600", "Captured plus repatriated"].map((c, j) => ({ text: c, options: { bold: true, fill: { color: NAVY }, color: WHITE, align: j === 1 ? "right" : "left", fontSize: 12.5 } })),
  ];
  s.addTable(rows, { x: MX, y: 1.95, w: 11.9, colW: [4.6, 3.0, 4.3], fontFace: BODY, border: { type: "solid", pt: 0.5, color: PANEL }, valign: "middle", rowH: 0.55 });
  s.addText("Circa 62,600 each way fills a daily A321XLR (182 seats) in peak season. Capture is bounded at 65% of the leaked pool, so the figure does not over-reach.",
    { x: MX, y: 5.5, w: 11.9, h: 0.5, fontSize: 11.5, fontFace: BODY, color: NAVY2, italic: true, margin: 0, valign: "top" });
  sourceLine(s, "Avia QSI catchment and repatriation model (Sabre O&D), to be refreshed on the live base.");
  footer(s, "The forecast");
}

// ---- capacity / economics
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  title(s, "Capacity and economics", "A daily aircraft in peak, with an honest read on the cost base");
  statCard(s, MX, 1.85, 3.55, 1.7, "132,500", "annual seats", "Daily A321XLR, two-way", NAVY);
  statCard(s, MX+3.75, 1.85, 3.55, 1.7, "circa 62%", "breakeven load factor", "Achievable on the demand forecast", BLUE);
  statCard(s, MX+7.5, 1.85, 3.55, 1.7, "Positive", "modest route margin", "At realistic entrant fares", GOLD);
  bullets(s, MX, 3.95, 11.9, 1.9, [
    "The forecast fills a daily A321XLR through the peak. Demand is concentrated in summer, so a building or seasonal pattern is the prudent launch shape.",
    "At realistic entrant fares (an economy yield set below the market to attract leaked traffic, plus a credible single-aisle business cabin) the route carries a modest positive margin with a breakeven near 62%.",
    "Honest caveat: the cost base is extrapolated for a new-generation narrowbody with no startup ramp modelled. The cost side should be pressure-tested before any commitment.",
  ], 12);
  sourceLine(s, "Avia QSI revenue and aircraft economics model. Illustrative; pressure-test the cost base before use.");
  footer(s, "The forecast");
}

// ===== SECTION 03
sectionDivider("03", "The case and\nthe precedent", "United A321XLR / Newark");

// ---- A321XLR enabler
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  title(s, "The A321XLR makes a thin route viable", "The aircraft that opens secondary-city transatlantic markets");
  statCard(s, MX, 1.85, 3.55, 1.7, "4,700nm", "A321XLR range", "Genoa to New York is circa 3,750nm", NAVY);
  statCard(s, MX+3.75, 1.85, 3.55, 1.7, "circa 182", "seats", "A fraction of a widebody's demand need", BLUE);
  statCard(s, MX+7.5, 1.85, 3.55, 1.7, "2025-26", "transatlantic entry", "Aer Lingus, Iberia, JetBlue, United", TEAL);
  bullets(s, MX, 3.95, 11.9, 1.9, [
    "The A321XLR carries circa 180 to 200 passengers across the Atlantic, opening routes that no widebody could fill daily. That is exactly what a thin market like Genoa needs.",
    "Genoa to New York is roughly 3,750nm, comfortably inside the type's 4,700nm range, and Genoa's runway and apron handle the aircraft without constraint.",
    "European carriers are already flying the type transatlantic, and United took its first A321XLR at Newark in June 2026, the natural operator for this route.",
  ], 12.5);
  sourceLine(s, "Airbus A321XLR; The Points Guy / Travel And Tour World (Aer Lingus, Iberia, JetBlue); AeroXplorer (United XLR, Jun 2026).");
  footer(s, "The case");
}

// ---- precedent: United secondary Italy
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  title(s, "The precedent: United's secondary-Italy nonstops", "A proven template Genoa fits precisely");
  const hdr = ["City", "Route", "Status", "Frequency"].map(t => ({ text: t, options: { bold: true, color: WHITE, fill: { color: NAVY }, align: "left", fontSize: 11.5 } }));
  const rows = [hdr];
  [["Naples", "Newark, plus Chicago, Atlanta", "Established, expanded 2024-2025", "Up to twice daily"],
   ["Palermo", "Newark (United, only US carrier)", "Launched May 2025", "3 weekly, building"],
   ["Bari", "Newark (United, only US carrier)", "Launches May 2026", "4 weekly, Boeing 767"],
   ["Genoa", "New York (proposed)", "The opportunity", "Seasonal, building"]].forEach((r, i) =>
    rows.push(r.map(c => ({ text: c, options: { fill: { color: i === 3 ? PANEL : (i % 2 ? LIGHT : WHITE) }, color: i === 3 ? NAVY : SLATE, bold: i === 3, align: "left", fontSize: 11.5 } }))));
  s.addTable(rows, { x: MX, y: 1.95, w: 11.9, colW: [2.0, 3.9, 3.6, 2.4], fontFace: BODY, border: { type: "solid", pt: 0.5, color: PANEL }, valign: "middle", rowH: 0.55 });
  s.addText("United is systematically opening Newark nonstops from secondary European cities (Palermo, Bari, Glasgow, Bilbao, Split) at 3 to 4 weekly. Genoa is a mid-sized Italian city with strong US leisure demand and no incumbent nonstop: the same case.",
    { x: MX, y: 4.95, w: 11.9, h: 0.9, fontSize: 12, fontFace: BODY, color: NAVY2, italic: true, margin: 0, valign: "top" });
  sourceLine(s, "Air Service One (May 2025); AFAR citing United (Oct 2025).");
  footer(s, "The case");
}

// ---- stimulation + seasonality (two panels)
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  title(s, "New traffic, and the right service pattern", "Stimulation as well as recapture, on a seasonal shape");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y: 1.95, w: 5.7, h: 3.8, fill: { color: LIGHT }, line: { color: PANEL, width: 1 }, rectRadius: 0.05 });
  s.addText("Stimulation, not only diversion", { x: MX+0.25, y: 2.1, w: 5.2, h: 0.4, fontSize: 14, fontFace: HEAD, color: NAVY, bold: true, margin: 0 });
  bullets(s, MX+0.25, 2.55, 5.2, 3.0, [
    "Naples is the proof: North American seats reached six times the 2019 level by 2025 as nonstops were added, growth too large to be diversion from Rome or Milan alone.",
    "A Genoa nonstop both recaptures the Liguria leakage to Milan and stimulates new US point-of-sale and inbound leisure demand.",
  ], 11.5);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX+5.95, y: 1.95, w: 5.65, h: 3.8, fill: { color: LIGHT }, line: { color: PANEL, width: 1 }, rectRadius: 0.05 });
  s.addText("A seasonal shape is the honest base", { x: MX+6.2, y: 2.1, w: 5.2, h: 0.4, fontSize: 14, fontFace: HEAD, color: NAVY, bold: true, margin: 0 });
  bullets(s, MX+6.2, 2.55, 5.2, 3.0, [
    "Mediterranean leisure is highly seasonal, so the prudent base case is a service running late April to October, not year-round.",
    "Year-round operation would lean on the visiting-friends and business layers, which are real but thinner. The precedent carriers run these markets seasonally.",
  ], 11.5);
  sourceLine(s, "Air Service One (Naples, May 2025); OAG (2024); Eurostat seasonality (2025).");
  footer(s, "The case");
}

// ---- airport
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  title(s, "Genoa Cristoforo Colombo airport", "Capable, growing fast, and with no long-haul today");
  statCard(s, MX, 1.85, 3.55, 1.7, "1.58m", "passengers, 2025", "A record, up 18% on 2024", NAVY);
  statCard(s, MX+3.75, 1.85, 3.55, 1.7, "2,915m", "runway", "Comfortable for an A321XLR to New York", BLUE);
  statCard(s, MX+7.5, 1.85, 3.55, 1.7, "Zero", "long-haul routes today", "All Liguria long-haul leaks out", GOLD);
  bullets(s, MX, 3.95, 11.9, 1.9, [
    "Genoa set a passenger record in 2025, up 18% on the year, with international traffic rising for 21 consecutive months. The airport has clear momentum.",
    "The runway and apron handle widebodies for cruise charters, so an A321XLR is well within capability. There is no transatlantic-relevant runway constraint.",
    "The airport is independently operated and is openly pursuing an air-service-development agenda, a receptive counterparty for a new long-haul.",
  ], 12.5);
  sourceLine(s, "Invest in Genova citing the airport (Jan 2026); Genoa Cristoforo Colombo airport / SKYbrary (runway).");
  footer(s, "The case");
}

// ---- business layer + methodology combined: business layer
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  title(s, "The business layer", "Modest but real, on top of the leisure and diaspora base");
  bullets(s, MX, 1.95, 7.2, 3.7, [
    "Liguria has an affluent, export-facing economy (GDP per head above the national average) anchored by the Port of Genoa, Italy's premier gateway port at circa 3.0m TEU in 2025.",
    "Genoa-headquartered industrials with global travel needs include Ansaldo Energia, Hitachi Rail and Esaote, alongside major Leonardo and Fincantieri sites in the region.",
    "The Italian Institute of Technology, headquartered in Genoa, runs permanent research outstations in the United States, generating recurring transatlantic academic travel.",
    "Italy-US goods and services trade reached circa $137.6bn in 2024, with New York the institutional hub for Italian business in the US.",
  ], 12);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX+7.5, y: 1.95, w: 4.1, h: 3.7, fill: { color: LIGHT }, line: { color: GOLD, width: 1 }, rectRadius: 0.05 });
  s.addText("Kept in proportion", { x: MX+7.7, y: 2.1, w: 3.7, h: 0.4, fontSize: 13, fontFace: HEAD, color: NAVY, bold: true, margin: 0 });
  s.addText("Genoa's specific corporate links to New York are modest. The route is carried by leisure, the diaspora and cruise demand, with business a supporting layer, not the headline.",
    { x: MX+7.7, y: 2.55, w: 3.7, h: 3.0, fontSize: 12, fontFace: BODY, color: SLATE, margin: 0, valign: "top" });
  sourceLine(s, "ISTAT (2024); Ports of Genoa (2025); IIT Facts and Figures (Apr 2026); US Department of Commerce / ITA (Feb 2026).");
  footer(s, "The case");
}

// ---- methodology
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  title(s, "Methodology: the Avia QSI approach", "The same engine, tuned to this route's profile");
  const steps = [
    ["Catchment", "Drive-time analysis sets Genoa's natural share of the Liguria market and the leakage to Milan, Rome and other gateways."],
    ["Demand and repatriation", "Sabre O&D sizes the New York market; a bounded capture of the leaked pool gives the demand a nonstop recaptures."],
    ["Service and economics", "The A321XLR is matched to demand, with revenue by cabin, fares, and aircraft operating economics for the route P&L."],
    ["Category research", "The relevance engine selects what matters for this profile: leisure, diaspora, cruise and the precedent, not corporate and tech."],
  ];
  steps.forEach(([t, d], i) => {
    const x = MX + (i%2)*5.95, y = 1.95 + Math.floor(i/2)*1.95;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 5.7, h: 1.75, fill: { color: LIGHT }, line: { color: PANEL, width: 1 }, rectRadius: 0.05, shadow: shadow() });
    s.addText(String(i+1), { x: x+0.2, y: y+0.18, w: 0.6, h: 0.6, fontSize: 24, fontFace: HEAD, color: GOLD, bold: true, margin: 0 });
    s.addText(t, { x: x+0.85, y: y+0.2, w: 4.6, h: 0.4, fontSize: 14, fontFace: HEAD, color: NAVY, bold: true, margin: 0 });
    s.addText(d, { x: x+0.85, y: y+0.62, w: 4.7, h: 1.05, fontSize: 11, fontFace: BODY, color: SLATE, margin: 0, valign: "top" });
  });
  s.addText("Data sources: Sabre O&D demand and OAG schedules. The category research is prioritised automatically by route profile.",
    { x: MX, y: 5.95, w: 11.9, h: 0.35, fontSize: 11, fontFace: BODY, color: NAVY2, italic: true, margin: 0 });
  footer(s, "The case");
}

// ---- close
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addText("A New York nonstop for Liguria", { x: MX, y: 2.1, w: 11.5, h: 1.0, fontSize: 36, fontFace: HEAD, color: WHITE, bold: true, margin: 0 });
  s.addText("The largest Italian-American market in the world, a record tourism region and a major cruise homeport, with circa 92,500 New York passengers a year leaking out through Milan. The A321XLR and United's secondary-city template make Genoa the next in line.",
    { x: MX, y: 3.3, w: 11.0, h: 1.6, fontSize: 15, fontFace: BODY, color: "C9D4E0", margin: 0, valign: "top" });
  s.addText([{ text: "Avia Solutions", options: { bold: true, color: GOLD, fontSize: 15, breakLine: true } },
    { text: "Route development and air service consultancy", options: { color: "AEBCCB", fontSize: 12, breakLine: true } },
    { text: "john.carter@aviasolutions.com", options: { color: "AEBCCB", fontSize: 12 } }],
    { x: MX, y: 5.3, w: 8, h: 1.1, fontFace: BODY, margin: 0, valign: "top" });
  pageNo++;
  s.addText(String(pageNo), { x: W - 1.0, y: H - 0.42, w: 0.5, h: 0.3, fontSize: 9, fontFace: BODY, color: "8FA0B3", align: "right", margin: 0 });
}

pres.writeFile({ fileName: "GOA-NYC_Route_Business_Case.pptx" }).then(f => console.log("Wrote", f));
