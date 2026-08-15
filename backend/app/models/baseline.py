import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

def train_baseline(df: pd.DataFrame):
    """
    Train a simple linear regression to predict next-day close price
    using MA_7, MA_21, Volatility, RSI as features.
    """
    df = df.copy()

    # Target: next day's close price
    df["Target"] = df["Close"].shift(-1)
    df = df.dropna()

    features = ["MA_7", "MA_21", "Daily_Return", "Volatility", "RSI"]
    X = df[features]
    y = df["Target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    model = LinearRegression()
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)

    # Predict tomorrow using the most recent row
    latest_features = X.iloc[[-1]]
    next_day_prediction = model.predict(latest_features)[0]

    return {
        "mae": mae,
        "next_day_prediction": next_day_prediction,
        "last_close": df["Close"].iloc[-1]
    }