import click
from qstrader.compat import queue
from soysauce.price_handler.iqfeed_csv_bar import IqfeedCsvBarPriceHandler
from soysauce.trading_session.backtest import Backtest
#config.OUTPUT_DIR
#config.CSV_DATA_DIR


def etf_run(): #config, testing, tickers, filename
    events_queue = queue.Queue()
    csv_dir = 'C:\\github\\SoySauceStock\\ipython'

    price_handler = IqfeedCsvBarPriceHandler(csv_dir, events_queue, ['EWZ'], 60)

    backtest = Backtest(price_handler)
    backtest.simulate_trading()

if __name__ == '__main__':
    etf_run()