from ai_brain import AIBrain


def test_ai_brain_returns_decision():
    brain = AIBrain()
    out = brain.evaluate({"trend": "up", "volatility": 1.1, "candles": []})
    assert "signal" in out and "risk" in out
