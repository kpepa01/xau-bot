"""Balanced strategy, connected to CRT/FVG helpers."""

from crt_patterns import detect_crt_patterns
from fvg_detector import detect_fvg


class BalancedStrategy:
    def generate(self, market_state: dict) -> dict:
        candles = market_state.get("candles", [])
        crt = detect_crt_patterns(candles)
        fvg = detect_fvg(candles)
        direction = "buy" if market_state.get("trend", "up") == "up" else "sell"
        confidence = 0.55 + (0.1 if crt["found"] else 0.0) + (0.1 if fvg.get("found") else 0.0)
        return {"direction": direction, "confidence": min(confidence, 0.95), "crt": crt, "fvg": fvg}
