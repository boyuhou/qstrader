import click
from qstrader.compat import queue
from soysauce.price_handler.iqfeed_csv_bar import IqfeedCsvBarPriceHandler
from soysauce.strategy.hybrid_frog_strategy import HybridFrogStrategy
from soysauce.order.frog_order import FrogOrder
from soysauce.trading_session.backtest import Backtest
#config.OUTPUT_DIR
#config.CSV_DATA_DIR


def etf_run(): #config, testing, tickers, filename
    events_queue = queue.Queue()
    tickers = ['EWZ', 'SPY', 'IWM']
    csv_dir = r'C:\temp\1minute\price'
    start_date = 20150101
    end_date = 20161101

    price_handler = IqfeedCsvBarPriceHandler(csv_dir, events_queue, tickers, 60, start_date, end_date)

    frog_factor_folder = r'C:\temp\daily\factor'
    frog_multiplier = 0.7
    frog_strategy = HybridFrogStrategy(tickers, events_queue, frog_factor_folder, frog_multiplier)
    frog_order = FrogOrder(r'C:\temp\FROG_TRADES.csv')

    backtest = Backtest(price_handler, frog_strategy, frog_order)
    backtest.simulate_trading()

if __name__ == '__main__':
    etf_run()