"""Signal model adapter connected to strategy modules."""

from balanced_strategy import BalancedStrategy
from high_winrate_strategy import HighWinrateStrategy


class SignalModel:
    def __init__(self) -> None:
        self.balanced = BalancedStrategy()
        self.high_wr = HighWinrateStrategy()

    def predict(self, market_state: dict) -> dict:
        b = self.balanced.generate(market_state)
        h = self.high_wr.generate(market_state)
        direction = h["direction"] if h.get("confidence", 0) >= b.get("confidence", 0) else b["direction"]
        confidence = max(h.get("confidence", 0), b.get("confidence", 0))
        return {"direction": direction, "confidence": confidence, "balanced": b, "high_wr": h}
