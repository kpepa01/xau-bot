"""Risk sizing helper functions."""


def scaled_risk_pct(base_risk_pct: float, balance: float, equity: float, max_drawdown_pct: float = 5.0) -> float:
    """Scale risk down as drawdown approaches/exceeds configured threshold."""
    if balance <= 0 or equity <= 0 or base_risk_pct <= 0:
        return 0.0
    dd_pct = max(0.0, ((balance - equity) / balance) * 100.0)
    if max_drawdown_pct <= 0:
        return max(0.0, float(base_risk_pct))
    scale = max(0.0, 1.0 - min(dd_pct / max_drawdown_pct, 1.0))
    return max(0.0, float(base_risk_pct) * scale)


def lot_from_risk(risk_amount: float, stop_distance: float, value_per_point: float) -> float:
    """Compute lot size from risk budget; never returns negative lot."""
    if risk_amount <= 0 or stop_distance <= 0 or value_per_point <= 0:
        return 0.0
    lot = risk_amount / (stop_distance * value_per_point)
    return max(0.0, float(lot))
