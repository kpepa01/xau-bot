"""FVG detector API used by strategy modules."""


def detect_fvg(candles: list) -> dict:
    if len(candles) < 3:
        return {"found": False, "gap": 0.0}
    c1, c2, c3 = candles[-3], candles[-2], candles[-1]
    bull_gap = c3.get("low", 0) > c1.get("high", 0)
    bear_gap = c3.get("high", 0) < c1.get("low", 0)
    if bull_gap:
        return {"found": True, "type": "bullish", "gap": c3.get("low", 0) - c1.get("high", 0)}
    if bear_gap:
        return {"found": True, "type": "bearish", "gap": c1.get("low", 0) - c3.get("high", 0)}
    return {"found": False, "gap": 0.0}
