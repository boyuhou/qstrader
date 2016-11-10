from .base import AbstractRiskManager
from ..event import MarketOrderEvent


class ExampleRiskManager(AbstractRiskManager):
    def refine_orders(self, portfolio, sized_order):
        """
        This ExampleRiskManager object simply lets the
        sized order through, creates the corresponding
        OrderEvent object and adds it to a list.
        """
        order_event = MarketOrderEvent(
            sized_order.ticker,
            sized_order.action,
            sized_order.quantity
        )
        return [order_event]
