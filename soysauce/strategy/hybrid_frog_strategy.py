from qstrader.strategy.base import AbstractStrategy
from qstrader.event import (SignalEvent, EventType)

class HybridFroggStrategy(AbstractStrategy):
    def __init__(self, tickers, event_queue, frog_score_path):