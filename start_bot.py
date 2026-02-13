#!/usr/bin/env python3
"""Bootstrap launcher for fully-automated bot startup.
Creates runtime folders and ensures Python dependencies before running `project`.
"""
import os
import sys
import subprocess
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNTIME_DIRS = [
    "config",
    "data",
    "logs",
    "reports",
    "fvg_data",
    "backtests",
    "cache",
    "models",
]

for d in RUNTIME_DIRS:
    (ROOT / d).mkdir(parents=True, exist_ok=True)

requirements = ROOT / "requirements.txt"
if requirements.exists():
    missing = [pkg for pkg in ("pandas", "numpy", "ta", "dotenv") if importlib.util.find_spec(pkg) is None]
    if missing:
        print(f"[bootstrap] missing deps detected: {missing}")
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements)]
        proc = subprocess.run(cmd, cwd=str(ROOT), check=False)
        if proc.returncode != 0:
            print("[bootstrap] dependency install failed (likely network/proxy restriction).")
            print("[bootstrap] please pre-install from requirements.txt in your deployment image.")

# Execute main bot file
os.execv(sys.executable, [sys.executable, str(ROOT / "project")])
