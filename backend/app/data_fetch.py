import yfinance as yf
import requests
from app.database import cache_analysis, get_cached_analysis
from app.nse_tickers import search_local
from app.charting import get_ohlc_data


def get_stock_data(ticker: str, period: str = "1mo", interval: str = "1d"):
    cache_key = f"data_{ticker}_{period}_{interval}"
    cached = get_cached_analysis(cache_key, max_age_minutes=5)
    if cached is not None:
        import pandas as pd
        df = pd.DataFrame(cached)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")
        return df

    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, interval=interval)
        if data.empty:
            raise ValueError("No data returned")

        cache_data = data.reset_index().copy()
        cache_data["Date"] = cache_data["Date"].astype(str)
        cache_analysis(cache_key, cache_data.to_dict(orient="records"))

        return data
    except Exception as e:
        raise RuntimeError(f"Unable to fetch data for {ticker}: {str(e)}")


def get_company_info(ticker: str):
    cache_key = f"info_{ticker}"
    cached = get_cached_analysis(cache_key, max_age_minutes=15)
    if cached is not None:
        return cached

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        result = {
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

        cache_analysis(cache_key, result)
        return result
    except Exception:
        return {"error": "Data temporarily unavailable (rate limited). Please try again shortly."}


def get_stock_news(ticker: str, limit: int = 5):
    cache_key = f"news_{ticker}"
    cached = get_cached_analysis(cache_key, max_age_minutes=15)
    if cached is not None:
        return cached

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

        cache_analysis(cache_key, results)
        return results
    except Exception:
        return []


def get_chart_data(ticker: str, period: str = "6mo"):
    """
    Get OHLC candlestick data for the chart, cached for 5 minutes.
    """
    cache_key = f"chart_{ticker}_{period}"
    cached = get_cached_analysis(cache_key, max_age_minutes=5)
    if cached is not None:
        return cached

    data = get_ohlc_data(ticker, period=period)
    if data:
        cache_analysis(cache_key, data)
    return data


def search_ticker(query: str, limit: int = 5):
    local_results = search_local(query, limit)
    if local_results:
        return local_results

    cache_key = f"search_{query.lower()}"
    cached = get_cached_analysis(cache_key, max_age_minutes=1440)
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