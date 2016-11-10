import click
from qstrader.compat import queue
from soysauce.price_handler.iqfeed_csv_bar import IqfeedCsvBarPriceHandler
from soysauce.strategy.hybrid_frog_strategy import HybridFrogStrategy

from soysauce.trading_session.backtest import Backtest
#config.OUTPUT_DIR
#config.CSV_DATA_DIR


def etf_run(): #config, testing, tickers, filename
    events_queue = queue.Queue()
    tickers = ['EWZ', 'SPY']
    csv_dir = r'C:\temp\1minute\price\ETF'

    price_handler = IqfeedCsvBarPriceHandler(csv_dir, events_queue, tickers, 60)

    frog_factor_folder = r'C:\temp\daily\factor\ETF'
    frog_strategy = HybridFrogStrategy(tickers, events_queue, frog_factor_folder)

    backtest = Backtest(price_handler, frog_strategy)
    backtest.simulate_trading()

if __name__ == '__main__':
    etf_run()