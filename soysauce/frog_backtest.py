import click
from qstrader.compat import queue


#config.OUTPUT_DIR
#config.CSV_DATA_DIR


def etf_run(config, testing, tickers, filename):
    events_queue = queue.Queue()

