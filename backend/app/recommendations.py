import pandas as pd
from .data_fetch import get_stock_data
from .features import add_features

def generate_signals(df: pd.DataFrame) -> dict:
    """
    Generate buy/sell signals based on technical indicators
    Returns: dict with action (BUY/SELL/HOLD), score (0-100), and reasons
    """
    if df.empty or len(df) < 2:
        return {"action": "HOLD", "score": 50, "signals": []}
    
    latest = df.iloc[-1]
    signals = []
    scores = []
    
    # RSI Signal (14-period)
    if 'RSI' in df.columns:
        rsi = latest.get('RSI')
        if rsi is not None:
            if rsi < 30:
                signals.append({"type": "RSI", "value": f"{rsi:.2f}", "signal": "OVERSOLD - BUY SIGNAL"})
                scores.append(75)
            elif rsi > 70:
                signals.append({"type": "RSI", "value": f"{rsi:.2f}", "signal": "OVERBOUGHT - SELL SIGNAL"})
                scores.append(25)
            elif 40 < rsi < 60:
                signals.append({"type": "RSI", "value": f"{rsi:.2f}", "signal": "NEUTRAL"})
                scores.append(50)
    
    # Moving Average Crossover
    if 'MA_7' in df.columns and 'MA_21' in df.columns:
        ma7 = latest.get('MA_7')
        ma21 = latest.get('MA_21')
        if ma7 is not None and ma21 is not None:
            if ma7 > ma21:
                signals.append({"type": "MA_Cross", "signal": "Golden Cross - BULLISH"})
                scores.append(70)
            elif ma7 < ma21:
                signals.append({"type": "MA_Cross", "signal": "Death Cross - BEARISH"})
                scores.append(30)
    
    # Price vs MA Signal
    if 'MA_21' in df.columns:
        close = latest.get('Close')
        ma21 = latest.get('MA_21')
        if close is not None and ma21 is not None:
            if close > ma21 * 1.05:
                signals.append({"type": "Price_MA", "signal": "Price 5%+ above MA21 - Strong Uptrend"})
                scores.append(70)
            elif close < ma21 * 0.95:
                signals.append({"type": "Price_MA", "signal": "Price 5%+ below MA21 - Strong Downtrend"})
                scores.append(30)
    
    # Volatility Signal
    if 'Volatility' in df.columns:
        volatility = latest.get('Volatility')
        if volatility is not None:
            if volatility > 0.05:
                signals.append({"type": "Volatility", "value": f"{volatility*100:.2f}%", "signal": "HIGH volatility - Risky"})
                scores.append(40)
            elif volatility < 0.02:
                signals.append({"type": "Volatility", "value": f"{volatility*100:.2f}%", "signal": "LOW volatility - Stable"})
                scores.append(60)
    
    # Daily Return Signal
    if 'Daily_Return' in df.columns:
        ret = latest.get('Daily_Return')
        if ret is not None:
            if ret > 0.05:
                signals.append({"type": "Daily_Return", "value": f"{ret*100:.2f}%", "signal": "Strong positive momentum"})
                scores.append(65)
            elif ret < -0.05:
                signals.append({"type": "Daily_Return", "value": f"{ret*100:.2f}%", "signal": "Strong negative momentum"})
                scores.append(35)
    
    # Calculate final score
    final_score = sum(scores) / len(scores) if scores else 50
    
    # Determine action
    if final_score > 65:
        action = "BUY"
    elif final_score < 35:
        action = "SELL"
    else:
        action = "HOLD"
    
    return {
        "action": action,
        "score": round(final_score, 2),
        "signals": signals,
        "confidence": len(signals) / 6 * 100  # Based on number of confirming signals
    }

def get_recommendations(ticker: str) -> dict:
    """Get comprehensive recommendation for a stock"""
    try:
        df = get_stock_data(ticker, period="6mo")
        if df.empty:
            return {"error": "No data found"}
        
        df = add_features(df)
        df = df.dropna()
        
        if df.empty:
            return {"error": "Not enough data"}
        
        signal_data = generate_signals(df)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        change_percent = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
        
        return {
            "ticker": ticker,
            "action": signal_data["action"],
            "score": signal_data["score"],
            "confidence": signal_data["confidence"],
            "signals": signal_data["signals"],
            "current_price": round(latest['Close'], 2),
            "change_percent": round(change_percent, 2),
            "ma7": round(latest.get('MA_7', 0), 2),
            "ma21": round(latest.get('MA_21', 0), 2),
            "rsi": round(latest.get('RSI', 0), 2),
            "volatility": round(latest.get('Volatility', 0) * 100, 2)
        }
    except Exception as e:
        return {"error": str(e)}
