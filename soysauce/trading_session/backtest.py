from qstrader.compat import queue
from qstrader.event import EventType


class Backtest(object):
    def __init__(self, price_handler, strategy, order):
        self.price_handler = price_handler
        self.events_queue = price_handler.events_queue
        self.strategy = strategy
        self.order = order

    def _run_backtest(self):
        print('Running backtest...')

        while self.price_handler.continue_backtest:
            try:
                event = self.events_queue.get(False)
            except queue.Empty:
                self.price_handler.stream_next()
            else:
                if event is not None:
                    if event.type == EventType.BAR:
                        self.strategy.calculate_signals(event)
                    elif event.type == EventType.ORDER:
                        self.order.record_order(event)
                    else:
                        raise NotImplementedError(str.format("Unsupported event type '%s'", event.type))

        self.order.output_orders()

    def simulate_trading(self):
        self._run_backtest()