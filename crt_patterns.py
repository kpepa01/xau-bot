"""CRT pattern helper connected to strategy stack."""


def detect_crt_patterns(candles: list) -> dict:
    if not candles:
        return {"found": False, "pattern": None}
    last = candles[-1]
    body = abs(last.get("close", 0) - last.get("open", 0))
    wick = max(last.get("high", 0) - max(last.get("open", 0), last.get("close", 0)), min(last.get("open", 0), last.get("close", 0)) - last.get("low", 0))
    return {"found": wick > body and body > 0, "pattern": "wick_rejection" if wick > body and body > 0 else None}
