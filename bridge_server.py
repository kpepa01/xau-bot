"""Minimal bridge server facade for external integration."""

from ai_brain import AIBrain
from logger import get_logger


class BridgeServer:
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.brain = AIBrain()

    def handle_market_snapshot(self, snapshot: dict) -> dict:
        result = self.brain.evaluate(snapshot)
        self.logger.info("Bridge handled snapshot")
        return result
