"""Unified launcher that loads giant bot script and extension modules."""

from importlib.machinery import SourceFileLoader
from bridge_server import BridgeServer
from check_imports import run_import_check


def load_giant_bot(path: str = "project"):
    return SourceFileLoader("giant_bot", path).load_module()


def start() -> dict:
    checks = run_import_check()
    if not all(checks.values()):
        missing = [k for k, ok in checks.items() if not ok]
        raise RuntimeError(f"Import graph incomplete: {missing}")

    giant = load_giant_bot("project")
    server = BridgeServer()
    return {"giant_bot": giant, "bridge": server}


if __name__ == "__main__":
    start()
    print("Bot stack connected.")
