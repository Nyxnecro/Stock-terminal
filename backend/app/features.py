import pandas as pd

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical indicators to the stock dataframe.
    Expects columns: Open, High, Low, Close, Volume
    """
    df = df.copy()

    # Moving averages
    df["MA_7"] = df["Close"].rolling(window=7).mean()
    df["MA_21"] = df["Close"].rolling(window=21).mean()

    # Daily returns
    df["Daily_Return"] = df["Close"].pct_change()

    # Volatility (rolling std of returns)
    df["Volatility"] = df["Daily_Return"].rolling(window=7).std()

    # RSI (Relative Strength Index)
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    return df