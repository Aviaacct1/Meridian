"""Avia Cortex - airline IATA -> name reference, for the dashboard typeahead.
OAG carries only the 2-letter code, and there is no airline dataset in the stack, so this is a
curated map of the major carriers an airport would pitch to (full-service, low-cost, ultra-low-cost,
majors by region). Extend freely; unknown codes still work in the engine, they just show as the code.
"""
AIRLINES = {
    # UK / Ireland
    "BA": "British Airways", "VS": "Virgin Atlantic", "U2": "easyJet", "LS": "Jet2",
    "BY": "TUI Airways", "EI": "Aer Lingus", "FR": "Ryanair", "RK": "Ryanair UK",
    "ZB": "Wizz Air UK", "T3": "Eastern Airways", "LM": "Loganair",
    # Western Europe
    "LH": "Lufthansa", "AF": "Air France", "KL": "KLM", "IB": "Iberia", "AZ": "ITA Airways",
    "LX": "SWISS", "OS": "Austrian Airlines", "SN": "Brussels Airlines", "TP": "TAP Air Portugal",
    "SK": "SAS", "AY": "Finnair", "EW": "Eurowings", "VY": "Vueling", "TO": "Transavia France",
    "HV": "Transavia", "EN": "Air Dolomiti", "WK": "Edelweiss Air", "DE": "Condor",
    "DY": "Norwegian", "D8": "Norwegian Air International", "IB": "Iberia", "I2": "Iberia Express",
    "UX": "Air Europa", "NT": "Binter Canarias", "V7": "Volotea", "PC": "Pegasus (EU ops)",
    "BT": "airBaltic", "OU": "Croatia Airlines", "JU": "Air Serbia", "A3": "Aegean Airlines",
    "OA": "Olympic Air", "FB": "Bulgaria Air", "PS": "Ukraine International", "LO": "LOT Polish Airlines",
    "OK": "Czech Airlines", "RO": "TAROM", "JP": "Adria", "YW": "Air Nostrum",
    # Central / Eastern Europe LCC
    "W6": "Wizz Air", "W4": "Wizz Air Malta", "W9": "Wizz Air UK", "0B": "Blue Air",
    # North America
    "AA": "American Airlines", "DL": "Delta Air Lines", "UA": "United Airlines",
    "WN": "Southwest Airlines", "B6": "JetBlue", "AS": "Alaska Airlines", "NK": "Spirit Airlines",
    "F9": "Frontier Airlines", "G4": "Allegiant Air", "SY": "Sun Country", "AC": "Air Canada",
    "WS": "WestJet", "PD": "Porter Airlines", "TS": "Air Transat", "F8": "Flair Airlines",
    "Y4": "Volaris", "VB": "VivaAerobus", "AM": "Aeromexico", "4O": "Interjet",
    "HA": "Hawaiian Airlines", "MX": "Breeze Airways",
    # Middle East
    "EK": "Emirates", "EY": "Etihad Airways", "QR": "Qatar Airways", "SV": "Saudia",
    "GF": "Gulf Air", "WY": "Oman Air", "RJ": "Royal Jordanian", "ME": "Middle East Airlines",
    "MS": "EgyptAir", "XY": "flynas", "J9": "Jazeera Airways", "FZ": "flydubai", "KU": "Kuwait Airways",
    "6E": "IndiGo", "IX": "Air India Express",
    # Africa
    "ET": "Ethiopian Airlines", "SA": "South African Airways", "KQ": "Kenya Airways",
    "AT": "Royal Air Maroc", "TU": "Tunisair", "AH": "Air Algerie", "WB": "RwandAir",
    "KP": "ASKY", "DT": "TAAG Angola", "HF": "Air Cote d'Ivoire",
    # Asia
    "SQ": "Singapore Airlines", "CX": "Cathay Pacific", "JL": "Japan Airlines", "NH": "ANA",
    "KE": "Korean Air", "OZ": "Asiana Airlines", "TG": "Thai Airways", "MH": "Malaysia Airlines",
    "GA": "Garuda Indonesia", "PR": "Philippine Airlines", "BR": "EVA Air", "CI": "China Airlines",
    "JX": "STARLUX Airlines",
    "CA": "Air China", "MU": "China Eastern", "CZ": "China Southern", "HU": "Hainan Airlines",
    "AI": "Air India", "UK": "Vistara", "VN": "Vietnam Airlines", "CX": "Cathay Pacific",
    "AK": "AirAsia", "D7": "AirAsia X", "FD": "Thai AirAsia", "QZ": "Indonesia AirAsia",
    "TR": "Scoot", "3K": "Jetstar Asia", "5J": "Cebu Pacific", "VJ": "VietJet Air",
    "MM": "Peach", "GK": "Jetstar Japan", "7C": "Jeju Air", "TW": "T'way Air", "LJ": "Jin Air",
    "9C": "Spring Airlines", "BX": "Air Busan", "SL": "Thai Lion Air", "JT": "Lion Air",
    # Oceania
    "QF": "Qantas", "VA": "Virgin Australia", "JQ": "Jetstar", "NZ": "Air New Zealand",
    "FJ": "Fiji Airways", "PX": "Air Niugini",
    # Latin America
    "LA": "LATAM Airlines", "JJ": "LATAM Brasil", "AV": "Avianca", "CM": "Copa Airlines",
    "AR": "Aerolineas Argentinas", "AD": "Azul", "G3": "GOL", "H2": "Sky Airline",
    "AM": "Aeromexico", "P5": "Wingo", "VH": "Viva Air",
    # Charter / leisure
    "NO": "Neos", "IG": "Air Italy", "OR": "TUI fly Netherlands", "X3": "TUI fly Germany",
    "XG": "SunExpress Germany", "XQ": "SunExpress", "6B": "TUIfly Nordic",
}


def search(q, limit=8):
    """Return [{code,label}] for a code or name query; exact code first, then name matches."""
    q = (q or "").strip()
    if not q:
        return []
    qu = q.upper(); ql = q.lower()
    exact, code_part, name_part = [], [], []
    for code, name in AIRLINES.items():
        if code == qu:
            exact.append((code, name))
        elif code.startswith(qu):
            code_part.append((code, name))
        elif ql in name.lower():
            name_part.append((code, name))
    name_part.sort(key=lambda cn: cn[1])
    out = exact + code_part + name_part
    seen = set(); res = []
    for code, name in out:
        if code in seen:
            continue
        seen.add(code)
        res.append({"code": code, "label": f"{name} ({code})"})
        if len(res) >= limit:
            break
    return res
