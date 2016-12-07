import pandas as pd
import os
import datetime
from qstrader.strategy.base import AbstractStrategy
from qstrader.event import (MarketOrderEvent, EventType)

open_time = datetime.time(9, 31)
second_open_time = datetime.time(9,32)
close_time = datetime.time(16, 0)


class HybridFrogStrategy(AbstractStrategy):
    def __init__(
            self, ticker, event_queue, frog_score_folder,
            frog_multiplier, profit_taking_multiplier=1, is_trailing_stop=0, trailing_stop_multiplier=1
    ):
        self.ticker = ticker
        self.events_queue = event_queue
        self.frog_score_folder = frog_score_folder
        self.frog_multiplier = frog_multiplier
        self.profit_taking_multiplier=profit_taking_multiplier
        self.open_prices = {}
        self.frog_status = {}
        self.frog_trades = {}
        self.last_price_event = None
        self.is_trailing_stop = is_trailing_stop
        self.trailing_stop_muliplier = trailing_stop_multiplier
        self.frog_info = self.build_frog_score_data()

    def build_frog_score_data(self):
        return self._get_frog_score(self.ticker)

    def _get_frog_score(self, ticker):
        print(str.format('Get Frog Score for ticker: {0}', ticker))
        score_file_path = os.path.join(self.frog_score_folder, ticker + '.csv')
        score_df = pd.read_csv(score_file_path, index_col=0, parse_dates=True)
        score_df['LagFrog'] = score_df['FrogBox'].shift(1)
        score_df['LagFrog'] = score_df['FrogBox'].shift(1)
        score_df['LagAvgRange'] = score_df['AvgRange'].shift(1)
        score_df['Ticker'] = ticker
        return score_df[['Ticker', 'LagFrog', 'LagAvgRange']].dropna()

    def _handle_new_day_job(self, event):
        self.frog_status[event.time.date()] = 0
        self.open_prices[event.time.date()] = round(event.open_price, 2)

        #close old trades
        if self.last_price_event is not None and self.frog_status[self.last_price_event.time.date()] == 1:
            frog_trade = self.frog_trades[self.last_price_event.time.date()][-1]
            self.frog_status[self.last_price_event.time.date()] = 2
            trade_info = {
                'AvgRange': frog_trade.avg_range,
                'FrogBox': frog_trade.frog_box,
                'HybridFrog': frog_trade.get_hybrid_frog_box(),
                'FrogMultiplier': frog_trade.frog_multiplier,
                'ProfitTakingMultiplier': frog_trade.profit_multiplier,
                'EntryTime': frog_trade.event.time
            }
            market_order_signal = MarketOrderEvent(
                ticker=event.ticker,
                action=frog_trade.get_cover_direction(),
                price=self.last_price_event.close_price,
                time=self.last_price_event.time,
                info=trade_info
            )
            self.events_queue.put(market_order_signal)

    def calculate_signals(self, event):
        try:
            if self.last_price_event is None or self.last_price_event.time.date() != event.time.date():
                self._handle_new_day_job(event)

            frog_status = self._get_frog_play_status(event)
            self._analyze_event(frog_status, event)
            self.last_price_event = event
        except TypeError:
            print(str.format('Cannot calculate the order on this day. Ticker: {0}, Datetime: {1}', event.ticker, event.time))

    def _attempt_to_enter_frog_play(self, event):
        open_price = self._get_open_price(event)
        frog_box, avg_range = self._get_frog_info(event.time.date())

        hybrid_frog = round(frog_box * self.frog_multiplier, 2)
        long_price = round(open_price + hybrid_frog, 2)
        short_price = round(open_price - hybrid_frog, 2)

        trade_info = {
            'AvgRange': avg_range,
            'FrogBox': frog_box,
            'HybridFrog': hybrid_frog,
            'FrogMultiplier': self.frog_multiplier,
            'ProfitTakingMultiplier': self.profit_taking_multiplier,
            'OpenPrice': open_price,
            'EntryTime': event.time
        }

        if event.low_price <= long_price <= event.high_price:
            stop_price = long_price - frog_box
            target_price = long_price + self.profit_taking_multiplier * frog_box
            frog_trade = FrogTrade(
                event, frog_box, avg_range, self.frog_multiplier, self.profit_taking_multiplier,
                'LONG', stop_price, target_price, long_price
            )
            self._create_entry_trade(frog_trade, trade_info)
        elif event.low_price <= short_price <= event.high_price:
            stop_price = short_price + frog_box
            target_price = short_price - self.profit_taking_multiplier * frog_box
            frog_trade = FrogTrade(
                event, frog_box, avg_range, self.frog_multiplier, self.profit_taking_multiplier,
                'SHORT', stop_price, target_price, short_price
            )
            self._create_entry_trade(frog_trade, trade_info)

    def _create_entry_trade(self, frog_trade, trade_info):
        self.frog_trades[frog_trade.event.time.date()] = [frog_trade]
        self.frog_status[frog_trade.event.time.date()] = 1
        market_order_signal = MarketOrderEvent(
            ticker=frog_trade.event.ticker,
            action=frog_trade.direction,
            price=frog_trade.execute_price,
            target_price=frog_trade.target_price,
            stop_price=frog_trade.stop_price,
            time=frog_trade.event.time,
            info=trade_info
        )
        self.events_queue.put(market_order_signal)

    def _attempt_to_take_profit_or_stop_loss(self, event):
        frog_trade = self.frog_trades[event.time.date()][-1] # always get the last trade (should be only 1 trade)

        trade_info = {
            'AvgRange': frog_trade.avg_range,
            'FrogBox': frog_trade.frog_box,
            'HybridFrog': frog_trade.get_hybrid_frog_box(),
            'FrogMultiplier': frog_trade.frog_multiplier,
            'ProfitTakingMultiplier': frog_trade.profit_multiplier,
            'EntryTime': frog_trade.event.time
        }

        if event.low_price <= frog_trade.target_price <= event.high_price:
            self.frog_status[event.time.date()] = 2
            market_order_signal = MarketOrderEvent(
                ticker=event.ticker,
                action=frog_trade.get_cover_direction(),
                price=frog_trade.target_price,
                time=event.time,
                info=trade_info
            )
            self.events_queue.put(market_order_signal)
        elif event.low_price <= frog_trade.stop_price <= event.high_price:
            self.frog_status[event.time.date()] = 2
            market_order_signal = MarketOrderEvent(
                ticker=event.ticker,
                action=frog_trade.get_cover_direction(),
                price=frog_trade.stop_price,
                time=event.time,
                info=trade_info
            )
            self.events_queue.put(market_order_signal)

        if self.is_trailing_stop:
            long_update_price = event.low_price - self.trailing_stop_muliplier * frog_trade.frog_box
            short_update_price = event.high_price + self.trailing_stop_muliplier * frog_trade.frog_box
            if frog_trade.direction == 'LONG' and frog_trade.stop_price < long_update_price:
                frog_trade.stop_price = long_update_price
            if frog_trade.direction == 'SHORT' and frog_trade.stop_price > short_update_price:
                frog_trade.stop_price = short_update_price

    def _analyze_event(self, frog_status, event):
        if frog_status == 0:
            self._attempt_to_enter_frog_play(event)
        elif frog_status == 1:
            self._attempt_to_take_profit_or_stop_loss(event)
        else:
            return None

    def _get_frog_play_status(self, event):
        """
        Args:
            event: bar price event
        Returns:
            0 frog play not initilized et
            1 frog play entered
            2 frog play exit
        """
        try:
            return self.frog_status[event.time.date()]
        except KeyError:
            print(str.format('Ticker: {0}, Time: {1}', event.ticker, event.time))
            raise

    def _get_open_price(self, event):
        try:
            return self.open_prices[event.time.date()]
        except KeyError:
            print(str.format('Unable to get open price, Ticker: {0}, Datetime: {1}', event.ticker, event.time))

    def _get_long_short_price(self, open_price, frog_box, multiplier):
        long_price = round(open_price + frog_box * multiplier, 2)
        short_price = round(open_price - frog_box * multiplier, 2)
        return long_price, short_price

    def _get_frog_info(self, date_info):
        try:
            frog_info = self.frog_info
            return frog_info.get_value(pd.Timestamp(date_info), 'LagFrog'), frog_info.get_value(pd.Timestamp(date_info), 'LagAvgRange')
        except KeyError:
            print(str.format('Ticker: {0}, Time: {1}', self.ticker, date_info))


class FrogTrade(object):
    def __init__(self, event, frog_box, avg_range, frog_multiplier,
                 profit_multiplier, direction, stop_price, target_price, execute_price):
        self.event = event
        self.frog_box = frog_box
        self.avg_range = avg_range
        self.frog_multiplier = frog_multiplier
        self.profit_multiplier = profit_multiplier
        self.direction = direction
        self.stop_price = stop_price
        self.target_price = target_price
        self.execute_price = execute_price

    def get_hybrid_frog_box(self):
        return self.frog_box * self.frog_multiplier

    def get_cover_direction(self):
        if self.direction == 'LONG':
            return 'SHORT'
        return 'LONG'
