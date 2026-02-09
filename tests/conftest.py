import importlib.machinery
import importlib.util
import os
import sys
import types

import pytest


def _install_stub_modules():
    mt5 = types.ModuleType("MetaTrader5")
    mt5.TIMEFRAME_M5 = 1
    mt5.TIMEFRAME_M15 = 2
    mt5.TIMEFRAME_H1 = 3
    mt5.TIMEFRAME_H4 = 4
    mt5.ORDER_TYPE_BUY = 0
    mt5.ORDER_TYPE_SELL = 1
    mt5.TRADE_ACTION_DEAL = 1
    mt5.TRADE_ACTION_SLTP = 2
    mt5.TRADE_RETCODE_DONE = 10009
    mt5.TRADE_RETCODE_REJECT = 10010
    mt5.initialize = lambda *args, **kwargs: True
    mt5.login = lambda *args, **kwargs: True
    mt5.shutdown = lambda *args, **kwargs: True
    mt5.last_error = lambda: (0, "OK")
    mt5.symbol_info = lambda *args, **kwargs: types.SimpleNamespace(point=0.01)
    mt5.symbol_info_tick = lambda *args, **kwargs: types.SimpleNamespace(bid=100.0, ask=100.2)
    mt5.terminal_info = lambda: types.SimpleNamespace()
    mt5.account_info = lambda: types.SimpleNamespace(balance=10000, equity=10000, margin=0)
    mt5.positions_get = lambda *args, **kwargs: []
    mt5.history_deals_get = lambda *args, **kwargs: []
    sys.modules["MetaTrader5"] = mt5

    ta = types.ModuleType("ta")
    ta_trend = types.ModuleType("ta.trend")
    ta_volatility = types.ModuleType("ta.volatility")
    ta_momentum = types.ModuleType("ta.momentum")

    class _SeriesStub:
        def __init__(self, series):
            self._series = series

        def ema_indicator(self):
            return self._series

        def macd(self):
            return self._series

        def macd_signal(self):
            return self._series

        def average_true_range(self):
            return self._series

        def rsi(self):
            return self._series

        def stoch(self):
            return self._series

        def stoch_signal(self):
            return self._series

    ta_trend.EMAIndicator = lambda series, window: _SeriesStub(series)
    ta_trend.MACD = lambda series: _SeriesStub(series)
    ta_volatility.AverageTrueRange = lambda high, low, close, window: _SeriesStub(close)
    ta_volatility.BollingerBands = lambda close, window=20, window_dev=2: _SeriesStub(close)
    ta_momentum.RSIIndicator = lambda close, window=14: _SeriesStub(close)
    ta_momentum.StochasticOscillator = lambda high, low, close: _SeriesStub(close)

    sys.modules["ta"] = ta
    sys.modules["ta.trend"] = ta_trend
    sys.modules["ta.volatility"] = ta_volatility
    sys.modules["ta.momentum"] = ta_momentum


@pytest.fixture(scope="session")
def project_module():
    if importlib.util.find_spec("pandas") is None:
        pytest.skip("pandas is not installed in the test environment")
    os.environ.setdefault("BACKTEST_MODE", "1")
    os.environ.setdefault("XAU_BOT_BOOTSTRAP_FILES", "0")
    _install_stub_modules()
    path = os.path.join(os.path.dirname(__file__), "..", "project")
    loader = importlib.machinery.SourceFileLoader("xau_bot_project", path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules["xau_bot_project"] = module
    loader.exec_module(module)
    return module
