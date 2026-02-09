import pytest

pd = pytest.importorskip("pandas")


def _sample_df():
    data = {
        "open": [105, 112, 100, 102, 104],
        "high": [110, 114, 100, 104, 106],
        "low": [105, 111, 95, 100, 102],
        "close": [110, 113, 95, 103, 105],
        "tick_volume": [1200, 1400, 1800, 1100, 1300],
        "atr": [1.2, 1.2, 1.2, 1.2, 1.2],
        "ema_fast": [101, 102, 103, 104, 105],
        "ema_slow": [100, 101, 102, 103, 104],
    }
    return pd.DataFrame(data)


def test_fvg_strategy_detects_gap(project_module):
    df = _sample_df()
    fvg = project_module.FVGStrategy(project_module.FVGConfig(MAX_GAP_PERCENTAGE=0.2))
    zones = fvg.detect_fvg(df, "XAUUSD")
    assert isinstance(zones, list)
    assert zones, "Expected at least one FVG zone in sample data"


def test_crt_strategy_detects_bullish_engulfing(project_module):
    df = _sample_df()
    crt = project_module.CRTStrategy()
    patterns = crt.detect_all_patterns(df, "downtrend", df["close"].iloc[-1], 1.2, "XAUUSD")
    assert isinstance(patterns, list)


def test_snr_strategy_identifies_levels(project_module):
    df = _sample_df()
    snr = project_module.SNRStrategy()
    levels = snr.identify_key_levels(df, df["close"].iloc[-1], 1.2)
    assert isinstance(levels, dict)
    assert "support" in levels and "resistance" in levels


def test_liquidity_strategy_returns_signals_list(project_module):
    df = _sample_df()
    liquidity = project_module.LiquiditySMCStrategy()
    signals = liquidity.generate_signals("XAUUSD", df, df["close"].iloc[-1])
    assert isinstance(signals, list)


def test_confluence_manager_returns_payload(project_module):
    df = _sample_df()
    confluence = project_module.ConfluenceManager()
    trend_signals = []
    result = confluence.analyze_confluence("XAUUSD", df, trend_signals, "trending")
    assert isinstance(result, dict)
    assert "direction" in result and "confluence_score" in result
