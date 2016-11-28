import click
import os
import json
import pandas as pd
from qstrader.compat import queue
from soysauce.price_handler.iqfeed_csv_bar import IqfeedCsvBarPriceHandler
from soysauce.strategy.hybrid_frog_strategy import HybridFrogStrategy
from soysauce.order.frog_order import FrogOrder
from soysauce.trading_session.backtest import Backtest
#config.OUTPUT_DIR
#config.CSV_DATA_DIR


def etf_run(): #config, testing, tickers, filename
    events_queue = queue.Queue()
    # tickers = ['EWJ']
    with open(r'..\config.json') as config_file:
        configs = json.load(config_file)
        etf_list = pd.read_csv(configs['ETF'], index_col=0).index.tolist()
        stock_list = pd.read_csv(configs['STOCK'], index_col=0).index.tolist()
    tickers = etf_list + stock_list
    tickers = ['EWZ']

    csv_dir = r'C:\temp\1minute\price'
    # start_date = 20100217
    start_date = 20160101
    end_date = 20161122
    # frog_multiplier = 0.5
    # profit_multiplier = 0.5
    # frog_multipliers = [0.5,0.6,0.7,0.8,0.9,1]
    # profit_multipliers = [0.5,0.6,0.7,0.8,0.9]
    frog_multipliers = [0.7]
    profit_multipliers = [1.0]
    is_trailing_stop = 1
    trailing_stop_multipliers = [0.5]
    for frog_multiplier in frog_multipliers:
        for profit_multiplier in profit_multipliers:
            for trailing_stop_multiplier in trailing_stop_multipliers:
                for t in tickers:
                    if is_trailing_stop:
                        trail_stop_text = '{0:.0f}'.format(trailing_stop_multiplier * 100)
                    else:
                        trail_stop_text = 'None'
                    target_file = str.format(r'C:\temp\FROG_TRADES_{2}_{0:d}_{1:d}_HF{3:.0f}_Profit{4:.0f}_TrailStop{5}.csv',
                                             start_date, end_date, t, frog_multiplier * 100,
                                             profit_multiplier * 100, trail_stop_text)
                    # if os.path.exists(target_file):
                    #     continue
                    price_handler = IqfeedCsvBarPriceHandler(csv_dir, events_queue, t, 60, start_date, end_date)

                    frog_factor_folder = r'C:\temp\daily\factor'

                    frog_strategy = HybridFrogStrategy(
                        ticker=t,
                        event_queue=events_queue,
                        frog_score_folder=frog_factor_folder,
                        frog_multiplier=frog_multiplier,
                        profit_taking_multiplier=profit_multiplier,
                        is_trailing_stop=is_trailing_stop,
                        trailing_stop_multiplier=trailing_stop_multiplier
                    )
                    frog_order = FrogOrder(target_file)

                    backtest = Backtest(price_handler, frog_strategy, frog_order)
                    backtest.simulate_trading()

if __name__ == '__main__':
    etf_run()