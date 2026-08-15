import requests
import io
import csv

NSE_COMPANIES = []

def load_nse_companies():
    """
    Download NSE's official list of all listed equities once.
    Source: NSE's public archive (legitimate, free, no auth needed).
    """
    global NSE_COMPANIES
    try:
        url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        reader = csv.DictReader(io.StringIO(response.text))
        companies = []
        for row in reader:
            symbol = row.get("SYMBOL", "").strip()
            name = row.get("NAME OF COMPANY", "").strip()
            if symbol and name:
                companies.append({"symbol": f"{symbol}.NS", "name": name})

        NSE_COMPANIES = companies
        print(f"Loaded {len(NSE_COMPANIES)} NSE companies")
    except Exception as e:
        print(f"Failed to load NSE company list: {e}")
        NSE_COMPANIES = []


def search_local(query: str, limit: int = 5):
    """Search the full NSE list by company name or symbol (case-insensitive substring match)."""
    query_lower = query.lower().strip()
    if not query_lower or not NSE_COMPANIES:
        return []

    matches = [
        {"symbol": c["symbol"], "name": c["name"], "exchange": "NSI"}
        for c in NSE_COMPANIES
        if query_lower in c["name"].lower() or query_lower in c["symbol"].lower()
    ]
    return matches[:limit]