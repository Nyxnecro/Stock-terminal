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
    """
    Fetch company fundamentals. Uses fast_info first (lighter, less rate-limited),
    falls back to full info only if needed.
    Successes cached 30 min, failures cached only 1 min (so it retries sooner).
    """
    cache_key = f"info_{ticker}"
    cached = get_cached_analysis(cache_key, max_age_minutes=30)
    if cached is not None and "error" not in cached:
        return cached

    error_cache_key = f"info_error_{ticker}"
    recent_error = get_cached_analysis(error_cache_key, max_age_minutes=1)
    if recent_error is not None:
        return recent_error

    try:
        stock = yf.Ticker(ticker)
        fast = stock.fast_info

        result = {
            "name": None,
            "sector": None,
            "industry": None,
            "market_cap": fast.get("market_cap") if fast else None,
            "pe_ratio": None,
            "eps": None,
            "52_week_high": fast.get("year_high") if fast else None,
            "52_week_low": fast.get("year_low") if fast else None,
            "dividend_yield": None,
            "current_price": fast.get("last_price") if fast else None,
            "currency": fast.get("currency") if fast else None,
        }

        try:
            info = stock.info
            result["name"] = info.get("longName")
            result["sector"] = info.get("sector")
            result["industry"] = info.get("industry")
            result["pe_ratio"] = info.get("trailingPE")
            result["eps"] = info.get("trailingEps")
            result["dividend_yield"] = info.get("dividendYield")
        except Exception:
            pass

        cache_analysis(cache_key, result)
        return result
    except Exception:
        error_result = {"error": "Data temporarily unavailable (rate limited). Please try again shortly."}
        cache_analysis(error_cache_key, error_result)
        return error_result

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