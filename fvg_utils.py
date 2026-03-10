"""
FVG Utility Functions
For integration with existing bot modules
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging
from dataclasses import dataclass

logger = logging.getLogger("XAU_Bot_Pro_v16")

@dataclass
class FVGConfluence:
    """FVG Confluence Analysis Result"""
    has_fvg_signal: bool = False
    direction: Optional[str] = None
    strength: float = 0.0
    confluence_score: int = 0
    zone_count: int = 0
    fresh_zones: int = 0
    conflicting: bool = False
    trade_recommended: bool = False
    reason: str = ""

def confluence_fvg_signals(fvg_signals: List[Dict], trend_signals: List[Dict],
                          crt_signals: List[Dict], snr_signals: List[Dict],
                          market_regime: str) -> FVGConfluence:
    """
    Analyze confluence between FVG and other signals
    """
    result = FVGConfluence()
    
    if not fvg_signals:
        result.reason = "No FVG signals detected"
        return result
    
    result.zone_count = len(fvg_signals)
    result.fresh_zones = sum(1 for s in fvg_signals if s.get('fresh', False))
    
    strongest_fvg = max(fvg_signals, key=lambda x: x.get('strength', 0), default=None)
    
    if not strongest_fvg:
        result.reason = "No valid FVG signals"
        return result
    
    result.has_fvg_signal = True
    result.direction = 'buy' if strongest_fvg['type'] == 'bullish' else 'sell'
    result.strength = strongest_fvg.get('strength', 0.5)
    
    trend_confluence = _check_trend_confluence(strongest_fvg, trend_signals)
    crt_confluence = _check_crt_confluence(strongest_fvg, crt_signals)
    snr_confluence = _check_snr_confluence(strongest_fvg, snr_signals)
    
    result.confluence_score = (
        (1 if trend_confluence else 0) +
        (1 if crt_confluence else 0) +
        (1 if snr_confluence else 0) +
        1
    )
    
    result.conflicting = _check_conflicts(strongest_fvg, trend_signals, 
                                         crt_signals, snr_signals)
    
    result.trade_recommended = (
        result.confluence_score >= 3 and
        result.strength >= 0.6 and
        not result.conflicting and
        market_regime in ['trending', 'ranging']
    )
    
    if result.trade_recommended:
        result.reason = f"Strong FVG confluence: {result.confluence_score}/4 points"
    else:
        result.reason = f"Insufficient confluence: {result.confluence_score}/4 points"
    
    return result

def _check_trend_confluence(fvg_signal: Dict, trend_signals: List[Dict]) -> bool:
    """Check if FVG aligns with trend signals"""
    if not trend_signals:
        return False
    
    fvg_direction = 'buy' if fvg_signal['type'] == 'bullish' else 'sell'
    
    for signal in trend_signals:
        if signal.get('direction') == fvg_direction:
            return True
    
    return False

def _check_crt_confluence(fvg_signal: Dict, crt_signals: List[Dict]) -> bool:
    """Check if FVG aligns with CRT patterns"""
    if not crt_signals:
        return False
    
    fvg_direction = 'buy' if fvg_signal['type'] == 'bullish' else 'sell'
    
    for signal in crt_signals:
        if signal.get('direction') == fvg_direction:
            return True
    
    return False

def _check_snr_confluence(fvg_signal: Dict, snr_signals: List[Dict]) -> bool:
    """Check if FVG aligns with SNR levels"""
    if not snr_signals:
        return False
    
    fvg_direction = 'buy' if fvg_signal['type'] == 'bullish' else 'sell'
    
    for signal in snr_signals:
        if signal.get('direction') == fvg_direction:
            return True
    
    return False

def _check_conflicts(fvg_signal: Dict, trend_signals: List[Dict],
                    crt_signals: List[Dict], snr_signals: List[Dict]) -> bool:
    """Check for conflicts between FVG and other signals"""
    fvg_direction = 'buy' if fvg_signal['type'] == 'bullish' else 'sell'
    
    conflict_count = 0
    
    for signals, weight in [(trend_signals, 1), (crt_signals, 1), (snr_signals, 1)]:
        opposite_count = sum(1 for s in signals if s.get('direction') != fvg_direction)
        if opposite_count > 0:
            conflict_count += weight
    
    return conflict_count >= 2
