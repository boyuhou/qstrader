import numpy as np


class FrogOrder(object):
    def __init__(self, output_path):
        self.executed_trades = []
        self.output_path = output_path

    def record_order(self, event):
        if 'OpenPrice' not in event.info:
            frog_order = [f for f in self.executed_trades if f.ticker == event.ticker and f.entry_datetime == event.info['EntryTime']][0]
            frog_order.record_exit(event)
        else:
            frog_order = FrogOrderDetail(event)
            self.executed_trades.append(frog_order)

    def output_orders(self):
        with open(self.output_path, 'w') as f:
            f.write(FrogOrder.write_header())
            f.write(''.join([t.to_str() for t in self.executed_trades]))

    @staticmethod
    def write_header():
        return 'Ticker,EntryDate,EntryTime,Direction,EntryPrice,StopPrice,TargetPrice,ExitDate,ExitTime,' \
               'ExitPrice,AvgRange,FrogBox,HF,FrogMultiplier,ProfitMultiplier,OpenPrice,R\n'


class FrogOrderDetail(object):
    def __init__(self, event):
        self.ticker = event.ticker
        self.entry_datetime = event.time
        self.direction = event.action
        self.entry_price = event.price
        self.target_price = event.target_price
        self.stop_price = event.stop_price
        self.avg_range = event.info['AvgRange']
        self.frog_box = event.info['FrogBox']
        self.hybrid_frog = event.info['HybridFrog']
        self.frog_multiplier = event.info['FrogMultiplier']
        self.profit_taking_multiplier = event.info['ProfitTakingMultiplier']
        self.open_price = event.info['OpenPrice']
        self.exit_price = None
        self.exit_datetime = None
        self.initial_r = np.abs(self.stop_price - self.entry_price)
        self.profit = None
        self.actual_r = None

    def record_exit(self, event):
        self.exit_price = event.price
        self.exit_datetime = event.time

    def to_str(self):
        try:
            if self.exit_price is not None:
                self.profit = (self.exit_price - self.entry_price) if self.direction == 'LONG' else -1 * (self.exit_price - self.entry_price)
                self.actual_r = self.profit / self.initial_r
            str_result = str.format(
                '{0},{1},{2},{3},{4:.2f},{5:.2f},{6:.2f},{7},{8},{9:.2f},{10:.2f},{11:.2f},{12:.2f},{13:.2f},{14:.2f},{15:.2f},{16:.2f}\n',
                self.ticker,
                self.entry_datetime.date(),
                self.entry_datetime.time(),
                self.direction,
                round(self.entry_price, 2),
                round(self.stop_price, 2),
                round(self.target_price, 2),
                self.exit_datetime.date(),
                self.exit_datetime.time(),
                round(self.exit_price, 2),
                round(self.avg_range, 2),
                round(self.frog_box, 2),
                round(self.hybrid_frog, 2),
                round(self.frog_multiplier, 2),
                round(self.profit_taking_multiplier, 2),
                self.open_price,
                self.actual_r
            )
        except AttributeError:
            print(str.format(
                '{0},{1},{2},{3},{4:.2f},{5:.2f},{6:.2f},{7},{8},{9},{10},{11},{12},{13},{14},{15}\n',
                self.ticker,
                self.entry_datetime,
                self.entry_datetime,
                self.direction,
                round(self.entry_price, 2),
                round(self.stop_price, 2),
                round(self.target_price, 2),
                None,
                None,
                None,
                round(self.avg_range, 2),
                round(self.frog_box, 2),
                round(self.hybrid_frog, 2),
                round(self.frog_multiplier, 2),
                round(self.profit_taking_multiplier, 2),
                self.open_price)
            )
            print('The above order does not have a regular close price, hence we doesnt record it.')
            str_result = '' # for days that market doesnt close on regular time, exclude it.
        return str_result


