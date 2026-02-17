"""Import preflight checker for the bot script."""

from __future__ import annotations

import ast
from importlib.util import find_spec
from pathlib import Path

BOT_FILE = Path("project")
IGNORE_MODULES = {
    "os", "sys", "json", "csv", "subprocess", "importlib", "time", "math",
    "threading", "logging", "hashlib", "random", "re", "datetime", "typing",
    "collections", "dataclasses", "itertools", "types",
    "fvg_detector", "fvg_utils", "winsound",
}

PIP_NAME_MAP = {
    "dotenv": "python-dotenv",
}


def extract_top_level_imports(source: str) -> set[str]:
    tree = ast.parse(source)
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])

    return imports


def main() -> int:
    if not BOT_FILE.exists():
        print(f"❌ Bot source not found: {BOT_FILE}")
        return 1

    modules = sorted(extract_top_level_imports(BOT_FILE.read_text(encoding="utf-8")))
    missing: list[tuple[str, str]] = []

    for module_name in modules:
        if module_name in IGNORE_MODULES:
            continue
        if find_spec(module_name) is None:
            missing.append((module_name, PIP_NAME_MAP.get(module_name, module_name)))

    if not missing:
        print("✅ All bot imports are available.")
        return 0

    print("❌ Missing Python packages required by the bot:")
    for module_name, package_name in missing:
        print(f"   - import '{module_name}' -> pip package '{package_name}'")
    print("\nInstall with:\n   pip install -r requirements.txt")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
