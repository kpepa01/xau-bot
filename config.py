"""Shared config bridge for the giant bot script and extension modules."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class AppConfig:
    symbols: List[str] = field(default_factory=lambda: ["XAUUSD", "XAUJPY"])
    entry_tf: str = "M15"
    h1_tf: str = "H1"
    h4_tf: str = "H4"
    min_confluence_score: float = 2.0


APP_CONFIG = AppConfig()
