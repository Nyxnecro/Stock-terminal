import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler


class LSTMPredictor(nn.Module):
    def __init__(self, input_size, hidden_size=64, num_layers=2, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size, hidden_size, num_layers,
            batch_first=True, dropout=dropout
        )
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return out


def create_sequences(data, target_col_idx, seq_length=15):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i + seq_length])
        y.append(data[i + seq_length, target_col_idx])
    return np.array(X), np.array(y)


def train_lstm(df: pd.DataFrame, epochs: int = 200, seq_length: int = 15):
    """
    Train an LSTM using engineered features + volume + daily return,
    with dropout regularization, to predict next-day closing price.
    """
    feature_cols = ["Close", "MA_7", "MA_21", "RSI", "Volatility", "Daily_Return", "Volume"]
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required features: {missing}. Run add_features() first.")

    data = df[feature_cols].dropna().values
    if len(data) < seq_length + 10:
        raise ValueError("Not enough data to train LSTM (need more history)")

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(data)

    close_idx = feature_cols.index("Close")
    X, y = create_sequences(scaled, close_idx, seq_length)

    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
    X_test_t = torch.tensor(X_test, dtype=torch.float32)
    y_test_t = torch.tensor(y_test, dtype=torch.float32).unsqueeze(1)

    model = LSTMPredictor(input_size=len(feature_cols))
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=50, gamma=0.5)

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        output = model(X_train_t)
        loss = criterion(output, y_train_t)
        loss.backward()
        optimizer.step()
        scheduler.step()

    model.eval()

    close_min = scaler.data_min_[close_idx]
    close_max = scaler.data_max_[close_idx]

    def inverse_close(scaled_vals):
        return scaled_vals * (close_max - close_min) + close_min

    with torch.no_grad():
        test_predictions = model(X_test_t).numpy().flatten()
        actual = y_test_t.numpy().flatten()

        pred_prices = inverse_close(test_predictions)
        actual_prices = inverse_close(actual)
        mae = float(np.mean(np.abs(pred_prices - actual_prices)))

        last_sequence = scaled[-seq_length:].reshape(1, seq_length, len(feature_cols))
        last_sequence_t = torch.tensor(last_sequence, dtype=torch.float32)
        next_scaled = model(last_sequence_t).numpy().flatten()[0]
        next_price = float(inverse_close(next_scaled))

    return {
        "mae": mae,
        "next_day_prediction": next_price,
        "last_close": float(data[-1][close_idx]),
        "epochs_trained": epochs,
        "features_used": feature_cols
    }