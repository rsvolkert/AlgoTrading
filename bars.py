import os
import sys
import asyncio
from alpaca_trade_api.rest import TimeFrame
from alpaca_trade_api.rest_async import AsyncRest

NY = 'America/New_York'


async def get_historic_data_base(symbols, start, end, timeframe, live):
    if live:
        rest = AsyncRest(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'))
    else:
        rest = AsyncRest(os.getenv('PAPER_KEY'), os.getenv('PAPER_SECRET'))

    major = sys.version_info.major
    minor = sys.version_info.minor
    if major < 3 or minor < 6:
        raise Exception('asyncio is not supported in your python version')

    step_size = 1000
    results = []
    for i in range(0, len(symbols), step_size):
        tasks = []
        for symbol in symbols[i:i+step_size]:
            args = [symbol, start, end, timeframe.value] if timeframe else [symbol, start, end]
            tasks.append(rest.get_bars_async(*args))

            results.extend(await asyncio.gather(*tasks, return_exceptions=True))

    return dict(zip(symbols, results))


async def get_historic_bars(symbols, start, end, timeframe, live):
    return await get_historic_data_base(symbols, start, end, timeframe, live)


async def get_bars(symbols, start, end, live=True):
    timeframe = TimeFrame.Day
    return await get_historic_bars(symbols, start, end, timeframe, live)
