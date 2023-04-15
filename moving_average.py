import os
import asyncio
import statistics
import pandas as pd
import alpaca_trade_api as tradeapi
from bars import get_bars
from datetime import timedelta


class Crossover:
    def __int__(self, stocks_to_hold=150, live=True):
        self.stocks_to_hold = stocks_to_hold

        if live:
            url = 'https://api.alpaca.markets'
            key = os.getenv('ALPACA_KEY')
            secret = os.getenv('ALPACA_SECRET')
        else:
            url = 'https://paper-api.alpaca.markets'
            key = os.getenv('PAPER_KEY')
            secret = os.getenv('PAPER_SECRET')

        self.api = tradeapi.REST(key, secret, url, 'v2')
        self.assets = self.api.list_assets()
        self.assets = [asset for asset in self.assets if asset.tradable and asset.fractionable]

    @staticmethod
    def _get_rating(bar, price):
        price_change = price - bar[-20:].close[0]
        # calculate standard dev of past volumes
        past_volumes = bar[:-1][-19:].volume.to_list()
        volume_stdev = statistics.stdev(past_volumes)
        # data might be bad quality
        assert volume_stdev != 0, 'bad quality'
        # compare to change since yesterday
        volume_change = bar[-1:].volume[0] - bar[-2:].volume[0]
        volume_factor = volume_change / volume_stdev
        # calculate rating
        rating = price_change / bar[-20:].close[0] * volume_factor

        return rating

    def order(self):
        buy = pd.DataFrame()

        symbols = [asset.symbol for asset in self.assets]

        bars = asyncio.run(get_bars(symbols,
                                    (pd.Timestamp('now', tz='America/New_York') - timedelta(days=40)).date().isoformat(),
                                    pd.Timestamp('now', tz='America/New_York').date().isoformat()))

        for symbol in bars.keys():
            if isinstance(bars[symbol], Exception):
                continue
            bar = bars[symbol][1]
            # check if we got no data
            if bar.empty:
                continue
            # get price
            price = bar[-1:].close[0]
            # get moving averages
            ma20 = bar[-20:].close.mean()
            ma10 = bar[-10:].close.mean()
            # see if there is a crossover
            if ma10 > ma20:
                try:
                    rating = self._get_rating(bar, price)
                    buy = buy.append({'symbol': symbol, 'rating': rating}, ignore_index=True)
                except AssertionError:
                    continue
        buy = buy.sort_values('rating', ascending=False)
        buy.reset_index(inplace=True, drop=True)
        buy = buy[:self.stocks_to_hold]

        # buy same $ amount of each
        notional = int((float(self.api.get_account().buying_power) / buy.shape[0]) * 100) / 100

        # close positions
        self.api.close_all_positions()
        for symbol in buy.symbol.to_list():
            self.api.submit_order(symbol,
                                  side='buy',
                                  notional=notional)
