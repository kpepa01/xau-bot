"""High-level orchestrator that composes signal and risk modules."""

from signal_model import SignalModel
from risk_model import RiskModel
from logger import get_logger


class AIBrain:
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.signal_model = SignalModel()
        self.risk_model = RiskModel()

    def evaluate(self, market_state: dict) -> dict:
        signal = self.signal_model.predict(market_state)
        risk = self.risk_model.assess(market_state, signal)
        decision = {"signal": signal, "risk": risk}
        self.logger.info("AI decision generated")
        return decision
