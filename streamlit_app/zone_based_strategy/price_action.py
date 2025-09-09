import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trading_config as tc

class PriceAction:
    """Price action pattern detection module"""
    
    @staticmethod
    def detect_engulfing_pattern(df: pd.DataFrame, lookback: int = 3) -> Dict:
        """
        Detect bullish and bearish engulfing patterns
        Returns latest engulfing signals
        """
        if len(df) < 2:
            return {'bullish_engulfing': False, 'bearish_engulfing': False}
        
        recent_df = df.tail(lookback + 1)
        signals = []
        
        for i in range(1, len(recent_df)):
            current = recent_df.iloc[i]
            previous = recent_df.iloc[i-1]
            
            # Calculate body sizes
            current_body = abs(current['close'] - current['open'])
            previous_body = abs(previous['close'] - previous['open'])
            
            # Minimum body size check (in pips)
            pip_value = 0.0001
            min_body_size = tc.MIN_ENGULFING_BODY_PIPS * pip_value
            
            if current_body < min_body_size:
                continue
            
            # Bullish engulfing
            if (previous['close'] < previous['open'] and  # Previous red
                current['close'] > current['open'] and   # Current green
                current['open'] <= previous['close'] and # Opens below prev close
                current['close'] >= previous['open'] and # Closes above prev open
                current_body > previous_body):           # Larger body
                
                signals.append({
                    'type': 'bullish_engulfing',
                    'timestamp': current.name,
                    'strength': current_body / previous_body
                })
            
            # Bearish engulfing
            elif (previous['close'] > previous['open'] and  # Previous green
                  current['close'] < current['open'] and   # Current red
                  current['open'] >= previous['close'] and # Opens above prev close
                  current['close'] <= previous['open'] and # Closes below prev open
                  current_body > previous_body):           # Larger body
                
                signals.append({
                    'type': 'bearish_engulfing',
                    'timestamp': current.name,
                    'strength': current_body / previous_body
                })
        
        # Return most recent signals
        latest_bullish = any(s['type'] == 'bullish_engulfing' for s in signals[-3:])
        latest_bearish = any(s['type'] == 'bearish_engulfing' for s in signals[-3:])
        
        return {
            'bullish_engulfing': latest_bullish,
            'bearish_engulfing': latest_bearish,
            'signals': signals
        }
    
    @staticmethod
    def detect_wick_rejections(df: pd.DataFrame, zones: Dict, lookback: int = 5) -> Dict:
        """
        Detect wick rejections from zone levels
        Returns rejection signals for each zone
        """
        if df.empty or not zones:
            return {}
        
        recent_df = df.tail(lookback)
        rejections = {
            'fast_ma_rejections': [],
            'slow_ma_rejections': [],
            'trend_ma_rejections': []
        }
        
        for _, candle in recent_df.iterrows():
            body_top = max(candle['open'], candle['close'])
            body_bottom = min(candle['open'], candle['close'])
            body_size = body_top - body_bottom
            
            if body_size == 0:  # Skip doji candles
                continue
            
            # Check each zone
            for zone_name, zone_data in zones.items():
                if '_zone' not in zone_name:
                    continue
                
                zone_key = zone_name.replace('_zone', '_rejections')
                
                # Upper wick rejection (bearish signal)
                upper_wick = candle['high'] - body_top
                if (candle['high'] >= zone_data['lower'] and
                    candle['high'] <= zone_data['upper'] and
                    body_top < zone_data['center'] and
                    upper_wick > body_size * tc.WICK_REJECTION_RATIO):
                    
                    rejections[zone_key].append({
                        'type': 'bearish_rejection',
                        'timestamp': candle.name,
                        'wick_ratio': upper_wick / body_size if body_size > 0 else 0,
                        'zone_level': zone_data['center']
                    })
                
                # Lower wick rejection (bullish signal)
                lower_wick = body_bottom - candle['low']
                if (candle['low'] <= zone_data['upper'] and
                    candle['low'] >= zone_data['lower'] and
                    body_bottom > zone_data['center'] and
                    lower_wick > body_size * tc.WICK_REJECTION_RATIO):
                    
                    rejections[zone_key].append({
                        'type': 'bullish_rejection',
                        'timestamp': candle.name,
                        'wick_ratio': lower_wick / body_size if body_size > 0 else 0,
                        'zone_level': zone_data['center']
                    })
        
        return rejections
    
    @staticmethod
    def detect_inside_bars(df: pd.DataFrame, lookback: int = 10) -> Dict:
        """
        Detect inside bar patterns (compression before breakout)
        """
        if len(df) < 2:
            return {'inside_bars': [], 'current_inside_bar': False}
        
        recent_df = df.tail(lookback)
        inside_bars = []
        
        for i in range(1, len(recent_df)):
            current = recent_df.iloc[i]
            mother_bar = recent_df.iloc[i-1]
            
            # Inside bar: current high < mother high AND current low > mother low
            if (current['high'] < mother_bar['high'] and
                current['low'] > mother_bar['low']):
                
                inside_bars.append({
                    'timestamp': current.name,
                    'mother_bar_range': mother_bar['high'] - mother_bar['low'],
                    'inside_bar_range': current['high'] - current['low']
                })
        
        return {
            'inside_bars': inside_bars,
            'current_inside_bar': len(inside_bars) > 0 and inside_bars[-1]['timestamp'] == df.index[-1]
        }
    
    @staticmethod
    def detect_pin_bars(df: pd.DataFrame, lookback: int = 5) -> Dict:
        """
        Detect pin bar patterns (long wick, small body)
        """
        if df.empty:
            return {'pin_bars': []}
        
        recent_df = df.tail(lookback)
        pin_bars = []
        
        for _, candle in recent_df.iterrows():
            body_size = abs(candle['close'] - candle['open'])
            total_range = candle['high'] - candle['low']
            upper_wick = candle['high'] - max(candle['open'], candle['close'])
            lower_wick = min(candle['open'], candle['close']) - candle['low']
            
            if total_range == 0:  # Skip zero-range candles
                continue
            
            # Pin bar criteria
            body_ratio = body_size / total_range
            wick_threshold = 0.6  # Wick should be at least 60% of total range
            body_threshold = 0.3  # Body should be less than 30% of total range
            
            # Bullish pin bar (long lower wick)
            if (lower_wick / total_range > wick_threshold and
                body_ratio < body_threshold):
                
                pin_bars.append({
                    'type': 'bullish_pin',
                    'timestamp': candle.name,
                    'wick_ratio': lower_wick / total_range,
                    'body_ratio': body_ratio
                })
            
            # Bearish pin bar (long upper wick)
            elif (upper_wick / total_range > wick_threshold and
                  body_ratio < body_threshold):
                
                pin_bars.append({
                    'type': 'bearish_pin',
                    'timestamp': candle.name,
                    'wick_ratio': upper_wick / total_range,
                    'body_ratio': body_ratio
                })
        
        return {'pin_bars': pin_bars}
    
    @staticmethod
    def calculate_momentum(df: pd.DataFrame, period: int = 3) -> Dict:
        """
        Calculate recent price momentum
        """
        if len(df) < period:
            return {'momentum': 0, 'momentum_strength': 'WEAK'}
        
        recent_df = df.tail(period + 1)
        price_changes = recent_df['close'].diff().dropna()
        
        momentum = price_changes.sum()
        avg_momentum = price_changes.mean()
        
        # Classify momentum strength
        if abs(avg_momentum) > 0.001:  # Strong momentum (10+ pips average)
            strength = 'STRONG'
        elif abs(avg_momentum) > 0.0005:  # Medium momentum (5+ pips average)
            strength = 'MEDIUM'
        else:
            strength = 'WEAK'
        
        direction = 'BULLISH' if momentum > 0 else 'BEARISH' if momentum < 0 else 'NEUTRAL'
        
        return {
            'momentum': momentum,
            'avg_momentum': avg_momentum,
            'momentum_strength': strength,
            'momentum_direction': direction
        }
    
    @staticmethod
    def analyze_price_action_confluence(df: pd.DataFrame, zones: Dict) -> Dict:
        """
        Analyze confluence of multiple price action signals
        Returns combined signal strength
        """
        if df.empty:
            return {'confluence_score': 0, 'signal': 'NEUTRAL'}
        
        # Get all price action signals
        engulfing = PriceAction.detect_engulfing_pattern(df)
        rejections = PriceAction.detect_wick_rejections(df, zones)
        inside_bars = PriceAction.detect_inside_bars(df)
        pin_bars = PriceAction.detect_pin_bars(df)
        momentum = PriceAction.calculate_momentum(df)
        
        # Calculate confluence score
        bullish_signals = 0
        bearish_signals = 0
        
        # Engulfing patterns
        if engulfing['bullish_engulfing']:
            bullish_signals += 2
        if engulfing['bearish_engulfing']:
            bearish_signals += 2
        
        # Wick rejections (recent rejections only)
        for zone_rejections in rejections.values():
            recent_rejections = [r for r in zone_rejections if r['timestamp'] == df.index[-1]]
            for rejection in recent_rejections:
                if rejection['type'] == 'bullish_rejection':
                    bullish_signals += 1
                elif rejection['type'] == 'bearish_rejection':
                    bearish_signals += 1
        
        # Pin bars
        recent_pins = [p for p in pin_bars['pin_bars'] if p['timestamp'] == df.index[-1]]
        for pin in recent_pins:
            if pin['type'] == 'bullish_pin':
                bullish_signals += 1
            elif pin['type'] == 'bearish_pin':
                bearish_signals += 1
        
        # Momentum
        if momentum['momentum_direction'] == 'BULLISH' and momentum['momentum_strength'] != 'WEAK':
            bullish_signals += 1
        elif momentum['momentum_direction'] == 'BEARISH' and momentum['momentum_strength'] != 'WEAK':
            bearish_signals += 1
        
        # Determine overall signal
        net_signals = bullish_signals - bearish_signals
        if net_signals >= 2:
            signal = 'STRONG_BULLISH'
        elif net_signals == 1:
            signal = 'BULLISH'
        elif net_signals == -1:
            signal = 'BEARISH'
        elif net_signals <= -2:
            signal = 'STRONG_BEARISH'
        else:
            signal = 'NEUTRAL'
        
        return {
            'confluence_score': abs(net_signals),
            'signal': signal,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'components': {
                'engulfing': engulfing,
                'rejections': rejections,
                'inside_bars': inside_bars,
                'pin_bars': pin_bars,
                'momentum': momentum
            }
        }