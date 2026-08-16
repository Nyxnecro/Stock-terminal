import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
from typing import List, Dict

def get_ohlc_data(ticker: str, period: str = "5y", interval: str = "1d") -> List[Dict]:
    """
    Fetch OHLC (Open, High, Low, Close) data for charting
    Returns data in format compatible with TradingView Lightweight Charts
    """
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval)
        
        if df.empty:
            return []
        
        data = []
        for date, row in df.iterrows():
            timestamp = int(date.timestamp())
            data.append({
                "time": timestamp,
                "open": round(float(row['Open']), 2),
                "high": round(float(row['High']), 2),
                "low": round(float(row['Low']), 2),
                "close": round(float(row['Close']), 2),
                "volume": int(row['Volume'])
            })
        
        return sorted(data, key=lambda x: x['time'])
    except Exception as e:
        print(f"Error fetching OHLC data: {e}")
        return []

def get_volume_data(ticker: str, period: str = "1y", interval: str = "1d") -> List[Dict]:
    """Get volume data for volume chart"""
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval)
        
        if df.empty:
            return []
        
        data = []
        for date, row in df.iterrows():
            timestamp = int(date.timestamp())
            # Color based on close vs open
            color = '#10b981' if row['Close'] >= row['Open'] else '#ef4444'
            data.append({
                "time": timestamp,
                "value": int(row['Volume']),
                "color": color
            })
        
        return sorted(data, key=lambda x: x['time'])
    except Exception as e:
        print(f"Error fetching volume data: {e}")
        return []

def get_current_stats(ticker: str) -> Dict:
    """Get current price and stats"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1mo")
        
        if data.empty:
            return {}
        
        current = data.iloc[-1]
        previous = data.iloc[-2] if len(data) > 1 else current
        
        high_52w = stock.info.get('fiftyTwoWeekHigh', data['High'].max())
        low_52w = stock.info.get('fiftyTwoWeekLow', data['Low'].min())
        
        change = current['Close'] - previous['Close']
        change_percent = (change / previous['Close']) * 100 if previous['Close'] != 0 else 0
        
        return {
            "current": round(float(current['Close']), 2),
            "high_24h": round(float(data['High'].max()), 2),
            "low_24h": round(float(data['Low'].min()), 2),
            "volume": int(current['Volume']),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "high_52w": round(float(high_52w), 2),
            "low_52w": round(float(low_52w), 2)
        }
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return {}

def get_live_price(ticker: str) -> Dict:
    """Get latest price (simulated real-time)"""
    try:
        data = yf.Ticker(ticker).history(period="1d")
        if data.empty:
            return {}
        
        latest = data.iloc[-1]
        return {
            "price": round(float(latest['Close']), 2),
            "time": int(data.index[-1].timestamp()),
            "high": round(float(latest['High']), 2),
            "low": round(float(latest['Low']), 2),
            "volume": int(latest['Volume'])
        }
    except:
        return {}
