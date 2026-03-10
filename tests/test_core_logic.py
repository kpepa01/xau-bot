"""Unit tests for FVG detection, pattern recognition, and confluence scoring."""

import re
from pathlib import Path

import pandas as pd


SOURCE = Path("project").read_text(encoding="utf-8")


def _extract_embedded_module(name: str) -> str:
    match = re.search(rf"{name}\s*=\s*'''(.*?)'''", SOURCE, re.S)
    assert match, f"{name} not found"
    return match.group(1)


def _load_fvg_namespace():
    code = _extract_embedded_module("fvg_detector_code")
    ns = {}
    exec(code, ns)
    return ns


def _load_fvg_utils_namespace():
    code = _extract_embedded_module("fvg_utils_code")
    ns = {}
    exec(code, ns)
    return ns


def _load_crt_namespace():
    start = SOURCE.index("class CRTStrategy:")
    end = SOURCE.index("class SNRStrategy:")
    code = SOURCE[start:end]
    ns = {"pd": pd, "Tuple": tuple, "logger": type("L", (), {"logger": type("LL", (), {"info": staticmethod(lambda *_: None)})(), "log_crt_signal": staticmethod(lambda *_: None)})(), "config": type("C", (), {"CRT_PATTERNS": []})()}
    exec(code, ns)
    return ns


def test_fvg_detection_with_gap_data():
    ns = _load_fvg_namespace()
    strategy = ns["FVGStrategy"](ns["FVGConfig"]())

    df = pd.DataFrame(
        [
            {"open": 100.0, "high": 101.0, "low": 100.0, "close": 100.8, "tick_volume": 100},
            {"open": 101.0, "high": 104.0, "low": 101.0, "close": 103.7, "tick_volume": 250},
            {"open": 104.5, "high": 105.2, "low": 104.4, "close": 105.0, "tick_volume": 280},
            {"open": 104.9, "high": 106.0, "low": 104.7, "close": 105.8, "tick_volume": 300},
        ]
    )

    zones = strategy.detect_fvg(df, "XAUUSD")
    assert len(zones) >= 1
    assert zones[0].direction in {"bearish", "bullish", "partial"}


def test_pattern_recognition_hammer():
    ns = _load_crt_namespace()
    crt_cls = ns["CRTStrategy"]
    crt = crt_cls.__new__(crt_cls)

    candle = pd.Series({"open": 10.0, "close": 10.2, "high": 10.3, "low": 9.2})
    detected, confidence = crt.is_hammer(candle, prev_trend="downtrend")
    assert detected is True
    assert confidence > 0


def test_fvg_confluence_scoring():
    ns = _load_fvg_utils_namespace()
    fn = ns["confluence_fvg_signals"]

    result = fn(
        fvg_signals=[{"type": "bullish", "strength": 0.8, "fresh": True}],
        trend_signals=[{"direction": "buy"}],
        crt_signals=[{"direction": "buy"}],
        snr_signals=[{"direction": "buy"}],
        market_regime="trending",
    )

    assert result.has_fvg_signal is True
    assert result.confluence_score >= 3
    assert result.trade_recommended is True
