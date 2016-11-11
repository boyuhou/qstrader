import pandas as pd
import os
import datetime
from qstrader.strategy.base import AbstractStrategy
from qstrader.event import (SignalEvent, EventType)

open_time = datetime.time(9, 30)
close_time = datetime.time(16, 0)

class HybridFrogStrategy(AbstractStrategy):
    def __init__(self, tickers, event_queue, frog_score_folder, frog_multiplier, profit_taking_multiplier=1):
        self.tickers = tickers
        self.events_queue = event_queue
        self.frog_score_folder = frog_score_folder
        self.frog_multiplier = frog_multiplier
        self.profit_taking_multiplier=profit_taking_multiplier
        self.open_prices = {}
        self.frog_status = {}
        self.frog_trades = {}
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
            frog_status = self._get_frog_play_status(event)
            self._analyze_event(frog_status, event)

    def _attempt_to_enter_frog_play(self, event):
        open_price = self._get_open_price(event)
        frog_box, avg_range = self._get_frog_info(event.ticker, event.time.date())

        long_price = open_price + frog_box * self.frog_multiplier
        short_price = open_price - frog_box * self.frog_multiplier

        if event.ticker not in self.frog_trades:
            self.frog_trades[event.ticker] = {}

        if event.low_price <= long_price <= event.high_price:
            stop_price = long_price - frog_box
            target_price = long_price + self.profit_taking_multiplier * frog_box
            frog_trade = FrogTrade(
                event, frog_box, avg_range, self.frog_multiplier, self.profit_taking_multiplier,
                'LONG', stop_price, target_price, long_price
            )
            self._create_entry_trade(frog_trade)
        elif event.low_price <= short_price <= event.high_price:
            stop_price = short_price + frog_box
            target_price = short_price - self.profit_taking_multiplier * frog_box
            frog_trade = FrogTrade(
                event, frog_box, avg_range, self.frog_multiplier, self.profit_taking_multiplier,
                'SHORT', stop_price, target_price, short_price
            )
            self._create_entry_trade(frog_trade)

    def _create_entry_trade(self, frog_trade):
        self.frog_trades[frog_trade.event.ticker][frog_trade.event.time.date()] = [frog_trade]
        self.frog_status[frog_trade.event.ticker][frog_trade.event.time.date()] = 1
        #TODO raise signal

    def _attempt_to_take_profit_or_stop_loss(self, event):
        trade = self.frog_trades[event.event.ticker][event.time.date()]

        if event.time.time() == close_time:
            #TODO: raise signal with market close price
            self.frog_status[event.ticker][event.time.date()] = 2
        elif event.low_price <= trade.target_price <= event.high_price:
            #TODO: issue profit taking signal
            self.frog_status[event.ticker][event.time.date()] = 2
        elif event.low_price <= trade.stop_price <= event.high_price:
            #TODO: issue stop loss signal
            self.frog_status[event.ticker][event.time.date()] = 2

    def _analyze_event(self, frog_status, event):
        return {
            0: self._attempt_to_enter_frog_play(event),
            1: self._attempt_to_take_profit_or_stop_loss(event),
            2: None
        }[frog_status]

    def _get_frog_play_status(self, event):
        """
        Args:
            event: bar price event
        Returns:
            0 frog play not initilized et
            1 frog play entered
            2 frog play exit
        """
        if event.time.time() == open_time:
            if not self.frog_status.has_key(event.ticker):
                self.frog_status[event.ticker] = {}
            self.frog_status[event.ticker][event.time.date()] = 0
        return self.frog_status[event.ticker][event.time.date()]

    def _get_open_price(self, event):
        if event.time.time() == open_time:
            if event.ticker not in self.open_prices:
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


class FrogTrade(object):
    def __init__(self, event, frog_box, avg_range, frog_multiplier, profit_multiplier, direction, stop_price, target_price, execute_price):
        self.event = event
        self.frog_box = frog_box
        self.avg_range = avg_range
        self.frog_multiplier = frog_multiplier
        self.profit_multiplier = profit_multiplier
        self.direction = direction
        self.stop_price = stop_price
        self.target_price = target_price
        self.execute_price = execute_price



