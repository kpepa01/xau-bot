from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from risk_model import scaled_risk_pct, lot_from_risk


def test_property_scaled_risk_pct_is_bounded():
    for dd in range(0, 120, 3):
        balance = 10000.0
        equity = balance * (1 - dd / 100.0)
        risk_pct = scaled_risk_pct(1.0, balance, equity, max_drawdown_pct=5.0)
        assert 0.0 <= risk_pct <= 1.0


def test_property_lot_from_risk_never_negative():
    for risk_amount in [0, 1, 10, 100]:
        for stop in [0, 0.1, 1, 10]:
            for vpp in [0, 0.5, 1, 20]:
                lot = lot_from_risk(float(risk_amount), float(stop), float(vpp))
                assert lot >= 0.0
