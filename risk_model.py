"""Risk model wired to confluence/volatility context."""


class RiskModel:
    def assess(self, market_state: dict, signal: dict) -> dict:
        volatility = float(market_state.get("volatility", 1.0))
        confidence = float(signal.get("confidence", 0.0))
        mode = "normal"
        if volatility > 2.0:
            mode = "cautious"
        if confidence < 0.4:
            mode = "blocked"
        return {"mode": mode, "position_scale": 0.0 if mode == "blocked" else (0.5 if mode == "cautious" else 1.0)}
