"""Utility helpers for FVG scoring."""

from fvg_detector import detect_fvg


def score_fvg_context(candles: list) -> float:
    fvg = detect_fvg(candles)
    if not fvg.get("found"):
        return 0.0
    gap = float(fvg.get("gap", 0.0))
    return max(-0.45, min(0.45, gap)) if fvg.get("type") == "bullish" else -max(-0.45, min(0.45, gap))
