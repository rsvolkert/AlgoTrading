from alpaca_trade_api.rest import REST
from pandas import DataFrame

from model import get_data, load_model, predict

ALPACA_API_KEY = ""
ALPACA_SECRET_KEY = ""
BASE_URL = ""

api = REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, BASE_URL)


def get_buying_power():
    account = api.get_account()
    return float(account.cash)


def calculate_quantity(dollar_amount, current_price):
    qty = dollar_amount / current_price
    return round(qty, 4)


def submit_trade(symbol, qty, side):
    if side == "sell":
        try:
            api.get_position(symbol)
        except:
            return #TODO: log
        
    api.submit_order(
        symbol=symbol,
        qty=round(qty, 4),
        side=side,
        type="market",
        time_in_force="gtc"
    )


def trading_logic(symbol: str, df: DataFrame, current_price: float, qty: float, threshold: float = 0.01):
    model, scaler = load_model(symbol)

    predicted_price = predict(model, df, scaler)

    if predicted_price > current_price * (1+threshold):
        submit_trade(symbol, qty, "buy")
    elif predicted_price < current_price * (1-threshold):
        submit_trade(symbol, qty, "sell")
    else:
        pass #TODO: log no trade


def trade_many(symbols, allocation_per_stock=50, threshold=0.01):
    for symbol in symbols:
        try:
            df = get_data(symbol)
            if len(df) < 100:
                continue #TODO: log not enough data for symbol

            current_price = df["Close"].iloc[-1]

            qty = calculate_quantity(allocation_per_stock, current_price)

            trading_logic(symbol, df, current_price, qty, threshold)

        except Exception as e:
            pass #TODO: log exception


def main(threshold):
    stock_list = [] #TODO: make a list
    trade_many(stock_list, get_buying_power()/len(stock_list), threshold)


if __name__ == "__main__":
    pass #TODO: run main()
