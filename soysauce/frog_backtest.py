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

    csv_dir = r'C:\temp\1minute\price'
    start_date = 20100217
    # start_date = 20161108
    end_date = 20161109

    for t in tickers:
        target_file = str.format(r'C:\temp\FROG_TRADES_{2}_{0}_{1}.csv', str(start_date), str(end_date), t)
        if os.path.exists(target_file):
            continue
        price_handler = IqfeedCsvBarPriceHandler(csv_dir, events_queue, [t], 60, start_date, end_date)

        frog_factor_folder = r'C:\temp\daily\factor'
        frog_multiplier = 0.7
        frog_strategy = HybridFrogStrategy([t], events_queue, frog_factor_folder, frog_multiplier)
        frog_order = FrogOrder(str.format(r'C:\temp\FROG_TRADES_{2}_{0}_{1}.csv', str(start_date), str(end_date), t))

        backtest = Backtest(price_handler, frog_strategy, frog_order)
        backtest.simulate_trading()

if __name__ == '__main__':
    etf_run()