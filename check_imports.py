"""Import connectivity smoke-check for all bot modules."""

MODULES = [
    "config",
    "logger",
    "ai_brain",
    "signal_model",
    "risk_model",
    "balanced_strategy",
    "high_winrate_strategy",
    "crt_patterns",
    "fvg_detector",
    "fvg_utils",
    "bridge_server",
    "start_bot",
]


def run_import_check() -> dict:
    results = {}
    for name in MODULES:
        try:
            __import__(name)
            results[name] = True
        except Exception:
            results[name] = False
    return results


if __name__ == "__main__":
    r = run_import_check()
    failed = [k for k, ok in r.items() if not ok]
    if failed:
        raise SystemExit(f"Import check failed: {failed}")
    print("All imports connected.")
