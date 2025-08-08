import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM


def get_data(symbol: str):
    df = yf.download(symbol, period="2y", interval="1d")
    df = df[["Open", "High", "Low", "Close", "Volume"]]
    df.dropna(inplace=True)
    return df


def preprocess(df: pd.DataFrame, window_size=60):
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df)

    X, y = [], []
    for i in range(window_size, len(scaled_data)):
        X.append(scaled_data[i-window_size:i, 0])
        y.append(scaled_data[i, 0])

    X = np.array(X)
    y = np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1)) # samples, time steps, features

    return X, y, scaler


def create_model(input_shape: tuple):
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=input_shape))
    model.add(LSTM(units=50))
    model.add(Dense(units=1))
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model


def predict(model, data, scaler, window_size=60):
    last_data = data[-window_size:].values
    last_scaled = scaler.transform(last_data)
    X_input = np.reshape(last_scaled, (1, window_size, 1))
    pred_scaled = model.predict(X_input)
    pred_price = scaler.inverse_transform(pred_scaled)
    return pred_price[0][0]


def load_model(symbol: str):
    raise NotImplementedError


def main(symbol: str):
    df = get_data(symbol)
    X, y, scaler = preprocess(df)
    model = create_model((X.shape[1], 1))
    model.fit(X, y, epochs=10, batch_size=32)
