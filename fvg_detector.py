"""
Fair Value Gap Detection Module
Integrated with existing bot architecture
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger("XAU_Bot_Pro_v16")

@dataclass
class FVGConfig:
    """FVG Configuration aligned with existing bot structure"""
    ENABLED: bool = True
    MIN_CANDLE_BODY_RATIO: float = 0.8
    MAX_GAP_PERCENTAGE: float = 0.02
    GAP_FILTER_ATR_MULTIPLIER: float = 2.5
    FRESH_THRESHOLD_BARS: int = 50
    STRENGTH_VOLUME_MULTIPLIER: float = 1.5
    HTF_CONFIRMATION_REQUIRED: bool = True
    MIN_CONFLUENCE_LEVEL: int = 2
    MAX_AGE_BARS: int = 200
    PARTIAL_FVG_THRESHOLD: float = 0.3
    MITIGATION_LOOKBACK_BARS: int = 20
    GAP_STRENGTH_WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        'volume': 0.3,
        'gap_size': 0.25,
        'trend_alignment': 0.25,
        'snr_confluence': 0.2
    })
    
    USE_FVG_TP1: bool = True
    USE_FVG_TP2: bool = True
    SL_BREAKER_CANDLE_MULTIPLIER: float = 1.2
    MIN_STOP_DISTANCE_ATR_MULTIPLIER: float = 1.0

class FVGZone:
    """Represents a Fair Value Gap zone"""
    def __init__(self, start_bar: int, end_bar: int, high: float, low: float,
                 direction: str, gap_size: float, volume_score: float,
                 created_time: datetime):
        self.start_bar = start_bar
        self.end_bar = end_bar
        self.high = high
        self.low = low
        self.direction = direction
        self.gap_size = gap_size
        self.volume_score = volume_score
        self.created_time = created_time
        self.mitigated = False
        self.mitigation_time = None
        self.mitigation_price = None
        self.strength_score = 0.0
        self.confluence_score = 0
        self.htf_confirmed = False
        self.fresh = True
        self.partial = False
        
    def __repr__(self):
        return (f"FVGZone({self.direction}, high={self.high:.5f}, low={self.low:.5f}, "
                f"size={self.gap_size:.5f}, strength={self.strength_score:.2f}, "
                f"mitigated={self.mitigated}, fresh={self.fresh})")

class FVGStrategy:
    """Fair Value Gap Detection and Trading Strategy"""
    
    def __init__(self, config: FVGConfig = None):
        self.config = config or FVGConfig()
        self.detected_zones: Dict[str, List[FVGZone]] = defaultdict(list)
        self.active_zones: Dict[str, List[FVGZone]] = defaultdict(list)
        self.logger = logger
        
    def detect_fvg(self, df: pd.DataFrame, symbol: str) -> List[FVGZone]:
        """Detect Fair Value Gaps in price data"""
        if len(df) < 3:
            return []
        
        zones = []
        df = df.copy()
        
        # Calculate metrics
        df['body_size'] = abs(df['close'] - df['open'])
        df['high_low_range'] = df['high'] - df['low']
        df['body_ratio'] = df['body_size'] / df['high_low_range'].replace(0, 0.001)
        
        # Use tick_volume instead of volume
        if 'tick_volume' in df.columns:
            df['volume_avg'] = df['tick_volume'].rolling(20, min_periods=1).mean()
            df['volume_ratio'] = df['tick_volume'] / df['volume_avg'].replace(0, 0.001)
        else:
            df['volume_ratio'] = 1.0
        
        # Detect FVGs
        for i in range(2, len(df)):
            candle1 = df.iloc[i-2]
            candle2 = df.iloc[i-1]
            candle3 = df.iloc[i]

            # Ignore abnormal session/weekend gaps that often create false FVGs.
            recent_tr = (df['high'].iloc[max(0, i-20):i] - df['low'].iloc[max(0, i-20):i]).replace(0, np.nan)
            atr_proxy = float(np.nanmean(recent_tr)) if len(recent_tr) else 0.0
            open_gap = abs(float(candle3['open']) - float(candle2['close']))
            if atr_proxy > 0 and open_gap > (atr_proxy * self.config.GAP_FILTER_ATR_MULTIPLIER):
                continue
            
            if not self._validate_fvg_formation(candle1, candle2, candle3):
                continue
            
            # Determine direction
            if candle1['low'] > candle3['high']:
                direction = 'bullish'
                fvg_high = candle1['low']
                fvg_low = candle3['high']
            elif candle1['high'] < candle3['low']:
                direction = 'bearish'
                fvg_high = candle3['low']
                fvg_low = candle1['high']
            else:
                if self._is_partial_fvg(candle1, candle3):
                    direction = 'partial'
                    fvg_high = max(candle1['low'], candle3['high'])
                    fvg_low = min(candle1['low'], candle3['high'])
                else:
                    continue
            
            gap_size = fvg_high - fvg_low
            if gap_size <= 0:
                continue
            
            avg_price = (fvg_high + fvg_low) / 2
            gap_percentage = gap_size / avg_price
            
            if gap_percentage > self.config.MAX_GAP_PERCENTAGE:
                continue
            
            volume_score = self._calculate_volume_score(candle1, candle2, candle3, df, i)
            
            zone = FVGZone(
                start_bar=i-2,
                end_bar=i,
                high=fvg_high,
                low=fvg_low,
                direction=direction,
                gap_size=gap_size,
                volume_score=volume_score,
                created_time=datetime.now()
            )
            
            if direction == 'partial':
                zone.partial = True
                overlap = self._calculate_overlap(candle1, candle3)
                if overlap < self.config.PARTIAL_FVG_THRESHOLD:
                    continue
            
            zones.append(zone)
        
        self.clean_fvg_zones(symbol)
        
        if zones:
            self.detected_zones[symbol].extend(zones)
            self.logger.info(f"Detected {len(zones)} FVG zones for {symbol}")
        
        return zones
    
    def _validate_fvg_formation(self, candle1: pd.Series, candle2: pd.Series, 
                               candle3: pd.Series) -> bool:
        """Validate FVG formation criteria"""
        if candle2['close'] <= candle1['high'] and candle2['close'] >= candle1['low']:
            return False
        
        if candle1['body_ratio'] < self.config.MIN_CANDLE_BODY_RATIO:
            return False
        if candle3['body_ratio'] < self.config.MIN_CANDLE_BODY_RATIO:
            return False
        
        has_gap = (candle1['low'] > candle3['high']) or (candle1['high'] < candle3['low'])
        return has_gap
    
    def _is_partial_fvg(self, candle1: pd.Series, candle3: pd.Series) -> bool:
        """Check for partial FVG"""
        overlap_high = min(candle1['low'], candle3['high'])
        overlap_low = max(candle1['high'], candle3['low'])
        
        if overlap_high > overlap_low:
            overlap_size = overlap_high - overlap_low
            gap_size = abs(candle1['low'] - candle3['high'])
            return gap_size > overlap_size
        
        return False
    
    def _calculate_overlap(self, candle1: pd.Series, candle3: pd.Series) -> float:
        """Calculate overlap percentage"""
        overlap_high = min(candle1['low'], candle3['high'])
        overlap_low = max(candle1['high'], candle3['low'])
        
        if overlap_high > overlap_low:
            overlap_size = overlap_high - overlap_low
            candle1_range = candle1['low'] - candle1['high']
            candle3_range = candle3['high'] - candle3['low']
            avg_range = (abs(candle1_range) + abs(candle3_range)) / 2
            return overlap_size / avg_range if avg_range > 0 else 0
        
        return 0
    
    def _calculate_volume_score(self, candle1: pd.Series, candle2: pd.Series,
                               candle3: pd.Series, df: pd.DataFrame, current_idx: int) -> float:
        """Calculate volume-based score"""
        if 'volume_ratio' not in df.columns:
            return 0.5
        
        vol1 = df.iloc[current_idx-2]['volume_ratio']
        vol2 = df.iloc[current_idx-1]['volume_ratio']
        vol3 = df.iloc[current_idx]['volume_ratio']
        
        volume_confirmation = (vol1 > 1.0 or vol3 > 1.0)
        breaker_strength = 1.0 if vol2 > self.config.STRENGTH_VOLUME_MULTIPLIER else 0.5
        
        score = 0.0
        if volume_confirmation:
            score += 0.3
        score += breaker_strength * 0.3
        
        volume_trend = 1.0 if vol3 > vol1 else 0.5
        score += volume_trend * 0.4
        
        return min(1.0, score)
    
    def clean_fvg_zones(self, symbol: str):
        """Remove old and mitigated FVG zones"""
        if symbol not in self.detected_zones:
            return
        
        current_time = datetime.now()
        zones_to_keep = []
        
        for zone in self.detected_zones[symbol]:
            if zone.created_time and (current_time - zone.created_time).total_seconds() > \
               self.config.MAX_AGE_BARS * 300:
                continue
            
            if zone.mitigated and zone.mitigation_time:
                if (current_time - zone.mitigation_time).total_seconds() > 3600:
                    continue
            
            zones_to_keep.append(zone)
        
        self.detected_zones[symbol] = zones_to_keep
        self.logger.debug(f"Cleaned FVG zones for {symbol}, kept {len(zones_to_keep)} zones")
    
    def validate_fvg_with_trend(self, zone: FVGZone, trend_direction: str) -> float:
        """Validate FVG with trend alignment"""
        if trend_direction == 'uptrend' and zone.direction == 'bullish':
            return 0.8
        elif trend_direction == 'downtrend' and zone.direction == 'bearish':
            return 0.8
        elif trend_direction == 'sideways':
            return 0.6
        else:
            return 0.4
    
    def validate_fvg_with_snr(self, zone: FVGZone, support_levels: List[Dict],
                             resistance_levels: List[Dict]) -> float:
        """Validate FVG with Support/Resistance confluence"""
        score = 0.0
        
        if zone.direction == 'bullish':
            for support in support_levels[:3]:
                distance = abs(zone.low - support['price'])
                if distance < zone.gap_size * 2:
                    score += support['strength'] * 0.5
        else:
            for resistance in resistance_levels[:3]:
                distance = abs(zone.high - resistance['price'])
                if distance < zone.gap_size * 2:
                    score += resistance['strength'] * 0.5
        
        return min(1.0, score)
    
    def calculate_fvg_strength(self, zone: FVGZone, df: pd.DataFrame, 
                              trend_score: float, snr_score: float) -> float:
        """Calculate overall FVG strength score"""
        weights = self.config.GAP_STRENGTH_WEIGHTS
        
        gap_size_score = min(1.0, zone.gap_size / (df['close'].iloc[-1] * 0.01))
        volume_score = zone.volume_score
        
        strength = (
            gap_size_score * weights['gap_size'] +
            volume_score * weights['volume'] +
            trend_score * weights['trend_alignment'] +
            snr_score * weights['snr_confluence']
        )
        
        if zone.partial:
            strength *= 0.7
        
        zone.strength_score = strength
        return strength
    
    def check_mitigation(self, zone: FVGZone, current_price: float, 
                        current_bar: pd.Series) -> bool:
        """Check if FVG zone has been mitigated"""
        if zone.mitigated:
            return True
        
        if zone.direction == 'bullish':
            mitigated = current_bar['close'] < zone.low
            if mitigated:
                zone.mitigated = True
                zone.mitigation_time = datetime.now()
                zone.mitigation_price = current_price
        else:
            mitigated = current_bar['close'] > zone.high
            if mitigated:
                zone.mitigated = True
                zone.mitigation_time = datetime.now()
                zone.mitigation_price = current_price
        
        return zone.mitigated
    
    def get_active_fvg_zones(self, symbol: str, current_price: float,
                           lookback_bars: int = 100) -> List[FVGZone]:
        """Get active (unmitigated) FVG zones near current price"""
        if symbol not in self.detected_zones:
            return []
        
        active_zones = []
        current_time = datetime.now()
        
        for zone in self.detected_zones[symbol]:
            if zone.mitigated:
                continue
            
            if zone.created_time:
                hours_old = (current_time - zone.created_time).total_seconds() / 3600
                zone.fresh = hours_old < (self.config.FRESH_THRESHOLD_BARS * 5 / 60)
            
            price_distance = min(abs(current_price - zone.high), 
                               abs(current_price - zone.low))
            
            if price_distance < zone.gap_size * 3:
                active_zones.append(zone)
        
        active_zones.sort(key=lambda x: (x.strength_score, x.fresh), reverse=True)
        self.active_zones[symbol] = active_zones
        return active_zones
    
    def calculate_fvg_confluence(self, zone: FVGZone, confluence_data: Dict) -> int:
        """Calculate confluence score for FVG zone"""
        confluence_score = 0
        confluence_score += 1
        
        if zone.strength_score > 0.7:
            confluence_score += 1
        
        if zone.fresh:
            confluence_score += 1
        
        if zone.strength_score > 0.6:
            confluence_score += 1
        
        zone.confluence_score = confluence_score
        return confluence_score
    
    def get_fvg_trade_signals(self, symbol: str, df: pd.DataFrame, 
                             current_price: float, atr: float,
                             trend_direction: str, snr_levels: Dict) -> List[Dict]:
        """Generate trade signals from FVG zones"""
        signals = []
        active_zones = self.get_active_fvg_zones(symbol, current_price)
        
        for zone in active_zones:
            if zone.mitigated:
                continue
            
            is_approaching = self._is_price_approaching_fvg(zone, current_price, df)
            
            if is_approaching:
                trend_score = self.validate_fvg_with_trend(zone, trend_direction)
                snr_score = self.validate_fvg_with_snr(zone, 
                                                      snr_levels.get('support', []),
                                                      snr_levels.get('resistance', []))
                strength = self.calculate_fvg_strength(zone, df, trend_score, snr_score)
                
                if strength >= 0.6:
                    signal = self._create_fvg_signal(zone, current_price, atr, strength)
                    signals.append(signal)
        
        return signals
    
    def _is_price_approaching_fvg(self, zone: FVGZone, current_price: float,
                                 df: pd.DataFrame) -> bool:
        """Check if price is approaching the FVG zone"""
        if zone.direction == 'bullish':
            return current_price < zone.low and (zone.low - current_price) < zone.gap_size * 2
        else:
            return current_price > zone.high and (current_price - zone.high) < zone.gap_size * 2
    
    def _create_fvg_signal(self, zone: FVGZone, current_price: float,
                          atr: float, strength: float) -> Dict:
        """Create trade signal from FVG zone"""
        direction = 'buy' if zone.direction == 'bullish' else 'sell'
        
        if direction == 'buy':
            entry = zone.low
            sl = entry - atr * self.config.SL_BREAKER_CANDLE_MULTIPLIER
            tp1 = zone.low + (zone.gap_size / 2)
            tp2 = zone.high
        else:
            entry = zone.high
            sl = entry + atr * self.config.SL_BREAKER_CANDLE_MULTIPLIER
            tp1 = zone.high - (zone.gap_size / 2)
            tp2 = zone.low
        
        return {
            'symbol': 'XAUUSD',
            'direction': direction,
            'entry_price': entry,
            'sl_price': sl,
            'tp1_price': tp1 if self.config.USE_FVG_TP1 else None,
            'tp2_price': tp2 if self.config.USE_FVG_TP2 else None,
            'confidence': strength,
            'type': 'FVG',
            'zone_strength': zone.strength_score,
            'zone_fresh': zone.fresh,
            'confluence_score': zone.confluence_score,
            'gap_size': zone.gap_size
        }

def detect_fvg(df: pd.DataFrame, lookback_bars: int = 50) -> List[Dict]:
    """Detect Fair Value Gaps in price data (compatible function)"""
    if len(df) < 3:
        return []
    
    df_subset = df.tail(lookback_bars).copy()
    fvgs = []
    
    for i in range(2, len(df_subset)):
        candle1 = df_subset.iloc[i-2]
        candle2 = df_subset.iloc[i-1]
        candle3 = df_subset.iloc[i]
        
        if candle1['low'] > candle3['high']:
            fvg = {
                'type': 'bullish',
                'high': float(candle1['low']),
                'low': float(candle3['high']),
                'gap_size': float(candle1['low'] - candle3['high']),
                'start_idx': i-2,
                'end_idx': i,
                'volume_confirmation': True,
                'body_ratio': 0.8
            }
            fvgs.append(fvg)
        
        elif candle1['high'] < candle3['low']:
            fvg = {
                'type': 'bearish',
                'high': float(candle3['low']),
                'low': float(candle1['high']),
                'gap_size': float(candle3['low'] - candle1['high']),
                'start_idx': i-2,
                'end_idx': i,
                'volume_confirmation': True,
                'body_ratio': 0.8
            }
            fvgs.append(fvg)
    
    return fvgs

def clean_fvg_zones(fvg_zones: List[Dict], current_price: float, 
                   atr: float, max_age_bars: int = 100) -> List[Dict]:
    """Clean and filter FVG zones"""
    if not fvg_zones:
        return []
    
    cleaned = []
    
    for zone in fvg_zones:
        if zone.get('age_bars', 0) > max_age_bars:
            continue
        
        zone_mid = (zone['high'] + zone['low']) / 2
        distance = abs(current_price - zone_mid)
        
        if distance > atr * 3:
            continue
        
        if zone['type'] == 'bullish' and current_price > zone['high']:
            continue
        if zone['type'] == 'bearish' and current_price < zone['low']:
            continue
        
        cleaned.append(zone)
    
    return cleaned

def validate_fvg_with_trend(fvg_zone: Dict, trend_direction: str, 
                           trend_strength: float) -> float:
    """Validate FVG with trend alignment"""
    if trend_direction == 'neutral':
        return 0.5
    
    fvg_type = fvg_zone['type']
    
    if fvg_type == 'bullish' and trend_direction == 'uptrend':
        return 0.8 * trend_strength
    elif fvg_type == 'bearish' and trend_direction == 'downtrend':
        return 0.8 * trend_strength
    elif fvg_type == 'bullish' and trend_direction == 'downtrend':
        return 0.3
    elif fvg_type == 'bearish' and trend_direction == 'uptrend':
        return 0.3
    else:
        return 0.5

def validate_fvg_with_snr(fvg_zone: Dict, support_levels: List[Dict],
                         resistance_levels: List[Dict]) -> float:
    """Validate FVG with Support/Resistance confluence"""
    score = 0.0
    fvg_type = fvg_zone['type']
    
    if fvg_type == 'bullish':
        for support in support_levels[:3]:
            distance = abs(fvg_zone['low'] - support['price'])
            if distance < fvg_zone['gap_size']:
                score += support.get('strength', 0.5) * 0.5
    else:
        for resistance in resistance_levels[:3]:
            distance = abs(fvg_zone['high'] - resistance['price'])
            if distance < fvg_zone['gap_size']:
                score += resistance.get('strength', 0.5) * 0.5
    
    return min(1.0, score)

def calculate_fvg_strength(fvg_zone: Dict, volume_confirmation: bool,
                          trend_score: float, snr_score: float,
                          gap_size_normalized: float) -> float:
    """Calculate overall FVG strength"""
    weights = {
        'gap_size': 0.25,
        'volume': 0.25,
        'trend': 0.25,
        'snr': 0.25
    }
    
    volume_score = 1.0 if volume_confirmation else 0.5
    
    strength = (
        gap_size_normalized * weights['gap_size'] +
        volume_score * weights['volume'] +
        trend_score * weights['trend'] +
        snr_score * weights['snr']
    )
    
    return min(1.0, strength)
