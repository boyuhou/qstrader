import os
import pandas as pd
from qstrader.price_handler.base import AbstractBarPriceHandler
from qstrader.event import BarEvent


class IqfeedCsvBarPriceHandler(AbstractBarPriceHandler):
    def __init__(self, csv_dir, events_queue, init_tickers, period):
        self.csv_dir = csv_dir
        self.events_queue = events_queue
        self.continue_backtest = True
        self.tickers = {}
        self.tickers_data = {}
        self.period = period
        for ticker in init_tickers:
            self.subscribe_ticker(ticker)
        self.bar_stream = self._merge_sort_ticker_data()

    def subscribe_ticker(self, ticker):
        if ticker not in self.tickers:
            try:
                self._open_ticker_price_csv(ticker)
                self.tickers[ticker] = ticker
            except OSError:
                print(str.format('Could not subscribe ticker %s as no data CSV found for pricing', ticker))
        else:
            print(str.format('Could not subscribe ticker %s as no data CSV found for pricing', ticker))

    def stream_next(self):
        try:
            index, row = next(self.bar_stream)
            ticker = row['Ticker']
            tev = self._create_event(index, ticker, row)
            self.events_queue.put(tev)
        except StopIteration:
            self.continue_backtest = False

    def _open_ticker_price_csv(self, ticker):
        ticker_path = os.path.join(self.csv_dir, ticker + '.csv')
        price_df = pd.read_csv(ticker_path, index_col=0, parse_dates=True)
        price_df['Ticker'] = ticker
        self.tickers_data[ticker] = price_df
        return price_df

    def _merge_sort_ticker_data(self):
        return pd.concat(self.tickers_data.values()).sort_index().iterrows()

    def _create_event(self, index, ticker, row):
        open_price = row['Open']
        high_price = row['High']
        low_price = row['Low']
        close_price = row['Close']
        volume = int(row['Volume'])
        return BarEvent(ticker, index, self.period, open_price, high_price, low_price, close_price, volume)