"""Core logic tests using importable modules and deterministic fixtures."""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

pd = pytest.importorskip("pandas")

from fvg_detector import FVGConfig, FVGStrategy
from fvg_utils import confluence_fvg_signals
from crt_patterns import CRTStrategy

FIXTURES = Path(__file__).parent / "fixtures"


def test_fvg_detection_with_fixture_data():
    df = pd.read_csv(FIXTURES / "fvg_sample.csv")
    strategy = FVGStrategy(FVGConfig())
    zones = strategy.detect_fvg(df, "XAUUSD")
    assert zones
    assert zones[0].direction in {"bullish", "bearish", "partial"}


def test_pattern_recognition_hammer():
    crt = CRTStrategy.__new__(CRTStrategy)
    candle = pd.Series({"open": 10.0, "close": 10.2, "high": 10.3, "low": 9.2})
    detected, confidence = crt.is_hammer(candle, prev_trend="downtrend")
    assert detected is True
    assert confidence > 0


def test_fvg_confluence_scoring():
    result = confluence_fvg_signals(
        fvg_signals=[{"type": "bullish", "strength": 0.8, "fresh": True}],
        trend_signals=[{"direction": "buy"}],
        crt_signals=[{"direction": "buy"}],
        snr_signals=[{"direction": "buy"}],
        market_regime="trending",
    )
    assert result.has_fvg_signal is True
    assert result.confluence_score >= 3
    assert result.trade_recommended is True
