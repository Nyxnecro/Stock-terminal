import yfinance as yf
import requests
from app.database import init_db, cache_analysis, get_cached_analysis

def get_stock_data(ticker: str, period: str = "1mo", interval: str = "1d"):
    """
    Fetch historical stock data.
    """
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, interval=interval)
        if data.empty:
            raise ValueError("No data returned")
        return data
    except Exception as e:
        raise RuntimeError(f"Unable to fetch data for {ticker}: {str(e)}")
def get_company_info(ticker: str):
    """
    Fetch company fundamentals: market cap, PE ratio, sector, etc.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        return {
            "name": info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "eps": info.get("trailingEps"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
            "dividend_yield": info.get("dividendYield"),
            "current_price": info.get("currentPrice"),
            "currency": info.get("currency"),
        }
    except Exception as e:
        return {"error": "Data temporarily unavailable (rate limited). Please try again shortly."}

def get_stock_news(ticker: str, limit: int = 5):
    try:
        stock = yf.Ticker(ticker)
        news_items = stock.news[:limit]

        results = []
        for item in news_items:
            content = item.get("content", item)
            results.append({
                "title": content.get("title"),
                "publisher": content.get("provider", {}).get("displayName") if isinstance(content.get("provider"), dict) else content.get("publisher"),
                "link": content.get("canonicalUrl", {}).get("url") if isinstance(content.get("canonicalUrl"), dict) else content.get("link"),
                "published": content.get("pubDate", content.get("providerPublishTime")),
            })
        return results
    except Exception:
        return []

def search_ticker(query: str, limit: int = 5):
    """
    Search for a ticker by company name, prioritizing NSE/BSE listings.
    Uses cache to avoid repeated Yahoo Finance calls.
    """
    cache_key = f"search_{query.lower()}"
    cached = get_cached_analysis(cache_key)
    if cached is not None:
        return cached

    try:
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {"q": query, "quotesCount": limit, "newsCount": 0}
        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()

        results = []
        for quote in data.get("quotes", []):
            symbol = quote.get("symbol", "")
            if symbol.endswith(".NS") or symbol.endswith(".BO"):
                results.append({
                    "symbol": symbol,
                    "name": quote.get("longname") or quote.get("shortname"),
                    "exchange": quote.get("exchange"),
                })

        if results:
            cache_analysis(cache_key, results)

        return results
    except Exception:
        return []