// Avia Solutions - contract -> deck-data adapter.
// Turns one deck data contract (deck_contract.py output) into exactly the arrays the
// pptxgenjs deck builder needs, so the deck builds with NO manual data entry. Pure formatting;
// no number is changed. Any field the contract emits as null shows blank, so a route that has
// not yet filled a block (e.g. the home-feed connecting table) degrades gracefully.
const fs = require("fs");
function load(p){ return JSON.parse(fs.readFileSync(p, "utf8")); }

const f0 = n => (n == null ? "" : Math.round(n).toLocaleString("en-US"));          // 1,234
const k  = n => (n == null ? "" : (n / 1000).toFixed(1));                          // 000s
const pc = x => (x == null ? "" : (x * 100).toFixed(1) + "%");
const m  = n => (n == null ? "" : "$" + (n / 1e6).toFixed(1) + "m");
const d1 = n => (n == null ? "" : Number(n).toFixed(1));

function deckData(C) {
  const rm = C.route_metadata, ss = C.summary_and_schedule, sf = C.segment_forecast,
        rv = C.revenue_forecast, e = C.economics_year1, ch = C.connecting_at_hub,
        cd = C.connecting_at_destination, sm = sf.summary;

  const figs = [
    ["Point to point market", f0(ss.point_to_point_market)],
    ["Connecting market over " + rm.hub_airport, f0(ss.connecting_market_over_hub)],
    ["Connecting market over " + rm.destination_airport, f0(ss.connecting_market_over_destination)],
  ];

  const schedule = ss.schedule.map(s => [s.sector, s.dep_time || "", s.arr_time || "",
    s.operating_days, s.aircraft, f0(s.seats), f0(s.annual_seats), f0(s.annual_pax), pc(s.seat_factor)]);

  const seg = (sf.rows || []).map(r => [r.segment, k(r.base_annual_demand), pc(r.annual_growth_rate),
    k(r.demand_at_service_year), (r.stimulation_factor != null ? r.stimulation_factor.toFixed(2) : ""),
    k(r.demand_after_stimulation), pc(r.capture_rate), k(r.forecast), d1(r.pdew)]);

  const tot = (lbl, t) => [lbl, k(t.base_annual_demand), "", k(t.demand_at_service_year), "",
    k(t.demand_after_stimulation), pc(t.capture_rate), k(t.forecast), d1(t.pdew)];
  const segTotals = {
    p2p: tot("Point to point total", sm.point_to_point_total),
    cnxHub: tot("Connecting at " + ch.hub, sm.connecting_at_hub_total),
    cnxDest: tot("Connecting at " + cd.destination, sm.connecting_at_destination_total),
    grand: ["Grand total", "", "", "", "", "", pc(sm.grand_total.capture_rate), k(sm.grand_total.forecast), d1(sm.grand_total.pdew)],
  };

  const cnxHubCities = (ch.cities || []).map(c => [String(c.nr), c.city_code, c.city_name, c.country,
    f0(c.annual_demand), pc(c.airline_share), f0(c.annual_forecast), d1(c.pdew)]);
  const cnxHubTotal = ["", "", "Total (all markets)", "", f0(ch.total && ch.total.annual_demand),
    pc(sm.connecting_at_hub_total.capture_rate), f0(ch.total && ch.total.annual_forecast), d1(ch.total && ch.total.pdew)];
  const cnxDestCities = (cd.cities || []).map(c => [String(c.nr), c.city_code, c.city_name, c.country,
    f0(c.annual_demand), pc(c.airline_share), f0(c.annual_forecast), d1(c.pdew)]);

  const rev = {
    years: (rv.years || []).map(String),
    cap: (rv.annual_capacity || []).map(f0),
    pax: { p2p: rv.passengers.point_to_point.map(f0), cnxHub: rv.passengers.connecting_at_hub.map(f0),
           cnxDest: rv.passengers.connecting_at_destination.map(f0), total: rv.passengers.total.map(f0) },
    lf: (rv.implied_load_factor || rv.annual_capacity.map(() => null)).map(pc),
    revenue: { p2p: rv.revenue.point_to_point.map(m), cnxHub: (rv.revenue.connecting_at_hub || []).map(m),
               cnxDest: (rv.revenue.connecting_at_destination || []).map(m), cargo: rv.revenue.cargo.map(m),
               ancillary: rv.revenue.ancillary.map(m), total: rv.revenue.total.map(m) },
  };

  const econ = {
    equipment: e.equipment, weeklyDeps: e.weekly_departures, blockHrs: e.block_hours_per_departure,
    cabin: e.cabin_seats, totalSeats: e.total_seats, totalLF: pc(e.total_load_factor),
    fareP2P: e.avg_ow_fare_point_to_point != null ? "$" + f0(e.avg_ow_fare_point_to_point) : "",
    fareCnx: e.avg_ow_fare_connecting != null ? "$" + f0(e.avg_ow_fare_connecting) : "",
    fareBlend: e.avg_ow_fare_blended != null ? "$" + f0(e.avg_ow_fare_blended) : "",
    yield: e.yield_rev_per_rpk != null ? "$" + e.yield_rev_per_rpk.toFixed(3) : "",
    prask: e.prask != null ? "$" + e.prask.toFixed(4) : "",
    trask: e.trask != null ? "$" + e.trask.toFixed(4) : "",
    paxRev: m(e.passenger_revenue), cargoRev: m(e.cargo_revenue), ancRev: m(e.ancillary_revenue), totalRev: m(e.total_revenue),
    cask: e.cask != null ? "$" + e.cask.toFixed(4) : "", breakevenLF: pc(e.breakeven_load_factor),
  };

  const topMarkets = (C.catchment.top_markets_beyond_hub || []).map(x => [x.city, f0(x.annual_demand)]);

  return {
    meta: { airline: rm.airline_name, iata: rm.airline_iata, origin: rm.origin_airport, dest: rm.destination_airport,
            hub: rm.hub_airport, aircraft: rm.aircraft_type, seats: rm.seats, freq: rm.frequency_per_week,
            year: rm.service_year, distKm: rm.distance_km, distNm: rm.distance_nm },
    figs, schedule, seg, segTotals, cnxHubCities, cnxHubTotal, cnxDestCities, rev, econ, topMarkets,
  };
}

module.exports = { load, deckData, fmt: { f0, k, pc, m, d1 } };

if (require.main === module) {
  const C = load(process.argv[2] || "ba_lhr_sjc_deck_contract.json");
  const D = deckData(C);
  console.log("meta:", D.meta.airline, D.meta.origin + "-" + D.meta.dest, D.meta.aircraft, D.meta.seats + "seats");
  console.log("figs:", JSON.stringify(D.figs));
  console.log("seg rows:", D.seg.length, "| p2p total:", JSON.stringify(D.segTotals.p2p));
  console.log("cnx-hub cities:", D.cnxHubCities.length, "| rev total:", JSON.stringify(D.rev.revenue.total));
  console.log("econ LF/yield/PRASK/TRASK:", D.econ.totalLF, D.econ.yield, D.econ.prask, D.econ.trask);
}
