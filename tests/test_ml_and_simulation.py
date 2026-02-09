def test_ml_weight_optimizer_updates(project_module):
    optimizer = project_module.MLWeightOptimizer(
        learning_rate=0.2,
        decay=0.02,
        min_weight=0.05,
        max_weight=0.6,
    )
    base = {"trend_following": 0.4, "crt": 0.2, "snr": 0.2, "fvg": 0.1, "liquidity": 0.1}
    optimizer.record_trade("trending", {"trend_following": 1.0, "crt": 0.5}, "win")
    adjusted = optimizer.adjust_weights(base, "trending")
    assert abs(sum(adjusted.values()) - 1.0) < 1e-6
    assert all(0.05 <= value <= 0.6 for value in adjusted.values())


def test_error_simulation_rejects_orders(project_module):
    project_module.config.PAPER_ERROR_SIMULATION_ENABLED = True
    project_module.config.PAPER_ERROR_REJECT_RATE = 1.0
    engine = project_module.PaperTradingEngine(10000)
    result = engine.open_position("XAUUSD", "buy", 0.1, 100.0, 0.0, 0.0, "test")
    assert result.get("order") == 0
