Subject: QSI rebuild - two demand rules I need you to confirm (BA LHR-SJC)

Nick,

I've been rebuilding the QSI tool so it pulls the Sabre demand itself rather than us doing it by hand, and I'm validating it against your BA LHR-SJC work off the raw 2013 Sabre data. The tool now reads the full year and produces the same shape of extract you pulled, but two rules in how you built the demand are calls only you can confirm. Both are below with the numbers that make them concrete, so they should be quick to answer.

1. Which destinations count (market scope)

Your SFO/LAX/SAN extract is 6.12m passengers for 2013. Pulling California to every destination gives 49m, so you scoped it to the market a London hub actually competes for. Your extract covers 58 destination countries, Europe, India, the Middle East and parts of Africa, and excludes Asia-Pacific, US domestic and Latin America. The "direct" rows even go to the competing European gateways (CDG, FRA, AMS, ZRH), not only LHR, i.e. Californians you would want to win onto a LHR service.

Please confirm: is the in-scope destination set a fixed region or country list, and how do you decide it for a given route? Is it the same list every time, or does it shift with the hub or the target airline's network? This is the single biggest driver of the demand figure, so I want to codify your rule rather than guess at it.

2. How a carrier's passengers are counted (carrier attribution)

Your extract shows 711k BA passengers in this market. Counting only itineraries where BA is the single operating carrier gives about 513k. The gap is connecting passengers, for example someone on AA to New York then BA to London, where BA operates one leg. So you are crediting BA across the connecting legs, not just the headline carrier.

Please confirm: should a passenger count to BA if BA operates any leg, or markets any leg, and across all legs or only the long-haul leg over the hub? Marketing versus operating matters because the new Sabre data splits the two, where the old extract carried a single airline field.

3. Cabin labels (minor, for later)

Your extract uses six cabin labels (Discount Coach, Business, Coach, Discount Business, First, Discount First); the raw Sabre we now hold carries fewer. For the QSI demand it washes out, because we sum across cabin, but for the fare and revenue view we will need a mapping. If you have a standard cabin grouping, send it over; otherwise we will propose one and you can correct it.

Once you confirm 1 and 2 I can finalise the demand generator and start putting the rest of the historic forecasts through it. Happy to talk it through on a call if that is quicker.

Thanks,
John
