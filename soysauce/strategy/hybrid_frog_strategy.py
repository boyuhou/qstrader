import pandas as pd
import os
from qstrader.strategy.base import AbstractStrategy
from qstrader.event import (SignalEvent, EventType)


class HybridFrogStrategy(AbstractStrategy):
    def __init__(self, tickers, event_queue, frog_score_folder):
        self.tickers = tickers
        self.events_queue = event_queue
        self.frog_score_folder = frog_score_folder

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
        ticker = event.ticker
        time = event.time
        pass
