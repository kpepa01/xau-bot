from typing import Tuple
import pandas as pd

class CRTStrategy:
    """Systematic Candlestick Pattern Recognition with Trend Confirmation"""
    
    def __init__(self):
        self.patterns = config.CRT_PATTERNS
        logger.logger.info(f"CRT Strategy initialized with {len(self.patterns)} patterns")
    
    def is_hammer(self, candle: pd.Series, prev_trend: str = 'downtrend') -> Tuple[bool, float]:
        """Detect hammer pattern"""
        if prev_trend not in ['downtrend', 'sideways']:
            return False, 0.0
        
        body = abs(candle['close'] - candle['open'])
        upper_shadow = candle['high'] - max(candle['close'], candle['open'])
        lower_shadow = min(candle['close'], candle['open']) - candle['low']
        
        is_hammer = (lower_shadow > body * 2.0) and (upper_shadow < body * 0.5)
        
        if is_hammer:
            confidence = 0.75
            if candle.get('at_support', False):
                confidence = 0.85
            return True, confidence
        
        return False, 0.0
    
    def is_shooting_star(self, candle: pd.Series, prev_trend: str = 'uptrend') -> Tuple[bool, float]:
        """Detect shooting star pattern"""
        if prev_trend not in ['uptrend', 'sideways']:
            return False, 0.0
        
        body = abs(candle['close'] - candle['open'])
        upper_shadow = candle['high'] - max(candle['close'], candle['open'])
        lower_shadow = min(candle['close'], candle['open']) - candle['low']
        
        is_shooting_star = (upper_shadow > body * 2.0) and (lower_shadow < body * 0.5)
        
        if is_shooting_star:
            confidence = 0.75
            if candle.get('at_resistance', False):
                confidence = 0.85
            return True, confidence
        
        return False, 0.0
    
    def is_bullish_engulfing(self, prev_candle: pd.Series, current_candle: pd.Series, 
                           prev_trend: str = 'downtrend') -> Tuple[bool, float]:
        """Detect bullish engulfing pattern"""
        if prev_trend not in ['downtrend', 'sideways']:
            return False, 0.0
        
        prev_bearish = prev_candle['close'] < prev_candle['open']
        current_bullish = current_candle['close'] > current_candle['open']
        
        is_engulfing = (prev_bearish and current_bullish and 
                       current_candle['open'] < prev_candle['close'] and 
                       current_candle['close'] > prev_candle['open'])
        
        if is_engulfing:
            confidence = 0.80
            engulf_size = (current_candle['close'] - current_candle['open']) / prev_candle['body'] if prev_candle.get('body', 0) > 0 else 1
            if engulf_size > 1.5:
                confidence = 0.90
            return True, confidence
        
        return False, 0.0
    
    def is_bearish_engulfing(self, prev_candle: pd.Series, current_candle: pd.Series,
                           prev_trend: str = 'uptrend') -> Tuple[bool, float]:
        """Detect bearish engulfing pattern"""
        if prev_trend not in ['uptrend', 'sideways']:
            return False, 0.0
        
        prev_bullish = prev_candle['close'] > prev_candle['open']
        current_bearish = current_candle['close'] < current_candle['open']
        
        is_engulfing = (prev_bullish and current_bearish and 
                       current_candle['open'] > prev_candle['close'] and 
                       current_candle['close'] < prev_candle['open'])
        
        if is_engulfing:
            confidence = 0.80
            engulf_size = (prev_candle['open'] - current_candle['close']) / prev_candle['body'] if prev_candle.get('body', 0) > 0 else 1
            if engulf_size > 1.5:
                confidence = 0.90
            return True, confidence
        
        return False, 0.0
    
    def is_morning_star(self, first: pd.Series, second: pd.Series, third: pd.Series,
                       prev_trend: str = 'downtrend') -> Tuple[bool, float]:
        """Detect morning star pattern (3-candle bullish reversal)"""
        if prev_trend not in ['downtrend', 'sideways']:
            return False, 0.0
        
        first_bearish = first['close'] < first['open']
        second_small_body = abs(second['close'] - second['open']) < (abs(first['close'] - first['open']) * 0.3)
        third_bullish = third['close'] > third['open']
        
        is_morning_star = (first_bearish and second_small_body and third_bullish and
                          third['close'] > (first['open'] + first['close']) / 2)
        
        if is_morning_star:
            return True, 0.85
        
        return False, 0.0
    
    def is_evening_star(self, first: pd.Series, second: pd.Series, third: pd.Series,
                       prev_trend: str = 'uptrend') -> Tuple[bool, float]:
        """Detect evening star pattern (3-candle bearish reversal)"""
        if prev_trend not in ['uptrend', 'sideways']:
            return False, 0.0
        
        first_bullish = first['close'] > first['open']
        second_small_body = abs(second['close'] - second['open']) < (abs(first['close'] - first['open']) * 0.3)
        third_bearish = third['close'] < third['open']
        
        is_evening_star = (first_bullish and second_small_body and third_bearish and
                          third['close'] < (first['open'] + first['close']) / 2)
        
        if is_evening_star:
            return True, 0.85
        
        return False, 0.0
    
    def detect_all_patterns(self, df: pd.DataFrame, trend_direction: str, 
                          current_price: float, atr: float, symbol: str) -> List[Dict]:
        """Detect all candlestick patterns with trend confirmation"""
        if len(df) < 10:
            return []
        
        patterns = []
        current = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else None
        prev2 = df.iloc[-3] if len(df) >= 3 else None
        
        if prev is not None:
            prev = prev.copy()
            prev['body'] = abs(prev['close'] - prev['open'])
        
        # FIX: Use 'tick_volume' instead of 'volume'
        avg_volume = df['tick_volume'].rolling(10).mean().iloc[-1] if 'tick_volume' in df else 0
        volume_confirmation = current.get('tick_volume', 0) > avg_volume * 1.2 if avg_volume > 0 else False
        
        pattern_checks = [
            ('hammer', self.is_hammer(current, trend_direction)),
            ('shooting_star', self.is_shooting_star(current, trend_direction)),
        ]
        
        if prev is not None:
            pattern_checks.extend([
                ('bullish_engulfing', self.is_bullish_engulfing(prev, current, trend_direction)),
                ('bearish_engulfing', self.is_bearish_engulfing(prev, current, trend_direction)),
            ])
        
        if prev is not None and prev2 is not None:
            pattern_checks.extend([
                ('morning_star', self.is_morning_star(prev2, prev, current, trend_direction)),
                ('evening_star', self.is_evening_star(prev2, prev, current, trend_direction)),
            ])
        
        for pattern_name, (detected, confidence) in pattern_checks:
            if detected and confidence >= config.CRT_MIN_CONFIDENCE:
                direction = 'buy' if pattern_name in ['hammer', 'bullish_engulfing', 'morning_star'] else 'sell'
                
                pattern_data = {
                    'symbol': symbol,
                    'pattern': pattern_name,
                    'direction': direction,
                    'confidence': confidence,
                    'trend_direction': trend_direction,
                    'volume_confirmation': volume_confirmation,
                    'price': current_price,
                    'atr': atr
                }
                
                patterns.append(pattern_data)
                logger.log_crt_signal(pattern_data)
        
        return patterns

# ==================== SNR STRATEGY ====================

