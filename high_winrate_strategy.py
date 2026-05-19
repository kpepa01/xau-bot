"""High-winrate strategy connected to FVG utils."""

from fvg_utils import score_fvg_context


class HighWinrateStrategy:
    def generate(self, market_state: dict) -> dict:
        score = score_fvg_context(market_state.get("candles", []))
        direction = "buy" if score >= 0 else "sell"
        confidence = 0.5 + min(abs(score), 0.45)
        return {"direction": direction, "confidence": min(confidence, 0.95), "fvg_score": score}
