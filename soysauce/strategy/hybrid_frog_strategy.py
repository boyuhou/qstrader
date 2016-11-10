import pandas as pd
import os
import datetime
from qstrader.strategy.base import AbstractStrategy
from qstrader.event import (SignalEvent, EventType)

open_time = datetime.time(9, 30)

class HybridFrogStrategy(AbstractStrategy):
    def __init__(self, tickers, event_queue, frog_score_folder, frog_multiplier):
        self.tickers = tickers
        self.events_queue = event_queue
        self.frog_score_folder = frog_score_folder
        self.frog_multiplier = frog_multiplier
        self.open_prices = {}
        self.frog_infos = self.build_frog_score_data()

    def build_frog_score_data(self):
        score_dfs = [self._get_frog_score(t) for t in self.tickers]
        return pd.concat(score_dfs)

    def _get_frog_score(self, ticker):
        score_file_path = os.path.join(self.frog_score_folder, ticker + '.csv')
        score_df = pd.read_csv(score_file_path, index_col=0, parse_dates=True)
        score_df['LagFrog'] = score_df['FrogBox'].shift(1)
        score_df['LagFrog'] = score_df['FrogBox'].shift(1)
        score_df['LagAvgRange'] = score_df['AvgRange'].shift(1)
        score_df['Ticker'] = ticker
        return score_df[['Ticker', 'LagFrog', 'LagAvgRange']].dropna()

    def calculate_signals(self, event):
        if event.type == EventType.BAR:
            open_price = self._get_open_price(event)
            frog_box, avg_range = self._get_frog_info(event.ticker, event.time.date())

            long_price = open_price + frog_box * self.frog_multiplier
            short_price = open_price - frog_box * self.frog_multiplier

            # no frog play
            if event.low_price <= long_price and event.high_price >= long_price:
                self._create_long_signal()
            elif event.low_price <= short_price and event.high_price >= short_price:
                self._create_short_signal()

            # in frog play

            # done frog play

    def _get_open_price(self, event):
        if event.time.time() == open_time:
            if not self.open_prices.has_key(event.ticker):
                self.open_prices[event.ticker] = {}
            self.open_prices[event.ticker][event.time.date()] = event.close_price
        return self.open_prices[event.ticker][event.time.date()]

    def _get_long_short_price(self, open_price, frog_box, multiplier):
        long_price = open_price + frog_box * multiplier
        short_price = open_price - frog_box * multiplier
        return long_price, short_price

    def _get_frog_info(self, ticker, date_info):
        frog_info = self.frog_infos[self.frog_infos['Ticker'] == ticker]
        return frog_info.get_value(date_info, 'LagFrog'), frog_info.get_value(date_info, 'LagAvgRange')

    def _create_initial_hybrid_frog_signal(self, ticker, open_price, average_stat, frog_box, multiplier):
        long_order = SignalEvent()


