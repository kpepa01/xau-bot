from risk_model import RiskModel


def test_risk_blocked_low_confidence():
    rm = RiskModel()
    out = rm.assess({"volatility": 1.0}, {"confidence": 0.2})
    assert out["mode"] == "blocked"
