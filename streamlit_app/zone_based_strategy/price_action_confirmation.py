"""
Price Action Confirmation Module
Advanced candlestick pattern recognition and price action analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trading_config as tc

class PriceActionConfirmation:
    """
    Comprehensive price action analysis and pattern recognition
    """
    
    def __init__(self):
        self.pattern_methods = {
            'BASIC_PATTERNS': self._basic_candlestick_patterns,
            'REVERSAL_PATTERNS': self._reversal_patterns,
            'CONTINUATION_PATTERNS': self._continuation_patterns,
            'MOMENTUM_PATTERNS': self._momentum_patterns,
            'CONFLUENCE_PATTERNS': self._confluence_patterns,
            'COMPREHENSIVE': self._comprehensive_analysis
        }
    
    def analyze_price_action(self, df: pd.DataFrame, 
                            zones: Dict = None,
                            trend_data: Dict = None,
                            method: str = tc.PRICE_ACTION_METHOD) -> Dict:
        """
        Main entry point for price action analysis
        
        Args:
            df: OHLCV dataframe
            zones: Optional zone data for context
            trend_data: Optional trend analysis data
            method: Price action analysis method
            
        Returns:
            Dict with price action signals and confirmations
        """
        if method not in self.pattern_methods:
            raise ValueError(f"Unknown price action method: {method}")
        
        if df.empty or len(df) < tc.MIN_CANDLES_FOR_PATTERNS:
            return self._no_signal()
        
        # Run selected analysis method
        analysis_result = self.pattern_methods[method](df, zones, trend_data)
        
        # Add context information
        analysis_result.update({
            'current_price': df['close'].iloc[-1],
            'analysis_method': method,
            'candles_analyzed': len(df)
        })
        
        return analysis_result
    
    def _basic_candlestick_patterns(self, df: pd.DataFrame, zones: Dict = None, trend_data: Dict = None) -> Dict:
        """
        Basic single and double candlestick patterns
        """
        if len(df) < 2:
            return self._no_signal()
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        patterns_found = []
        total_confidence = 0
        
        # Single candle patterns
        single_patterns = self._detect_single_candle_patterns(latest)
        patterns_found.extend(single_patterns)
        
        # Double candle patterns
        double_patterns = self._detect_double_candle_patterns(prev, latest)
        patterns_found.extend(double_patterns)
        
        if patterns_found:
            # Calculate overall confidence
            pattern_confidences = [p['confidence'] for p in patterns_found]
            total_confidence = min(sum(pattern_confidences), 100)
            
            # Determine overall signal
            bullish_patterns = [p for p in patterns_found if p['direction'] == 'BULLISH']
            bearish_patterns = [p for p in patterns_found if p['direction'] == 'BEARISH']
            
            if len(bullish_patterns) > len(bearish_patterns):
                signal = 'BULLISH'
            elif len(bearish_patterns) > len(bullish_patterns):
                signal = 'BEARISH'
            else:
                signal = 'NEUTRAL'
        else:
            signal = 'NO_SIGNAL'
            total_confidence = 0
        
        return {
            'signal': signal,
            'confidence': total_confidence,
            'patterns_found': patterns_found,
            'pattern_count': len(patterns_found),
            'method': 'BASIC_PATTERNS'
        }
    
    def _reversal_patterns(self, df: pd.DataFrame, zones: Dict = None, trend_data: Dict = None) -> Dict:
        """
        Focus on reversal patterns, especially at zone boundaries
        """
        if len(df) < tc.REVERSAL_PATTERN_LOOKBACK:
            return self._no_signal()
        
        recent_candles = df.tail(tc.REVERSAL_PATTERN_LOOKBACK)
        
        reversal_patterns = []
        
        # Pin bar detection
        pin_bars = self._detect_pin_bars(recent_candles)
        reversal_patterns.extend(pin_bars)
        
        # Engulfing patterns
        engulfing_patterns = self._detect_engulfing_patterns(recent_candles)
        reversal_patterns.extend(engulfing_patterns)
        
        # Hammer and Doji patterns
        hammer_doji_patterns = self._detect_hammer_doji_patterns(recent_candles)
        reversal_patterns.extend(hammer_doji_patterns)
        
        # Morning/Evening star patterns
        star_patterns = self._detect_star_patterns(recent_candles)
        reversal_patterns.extend(star_patterns)
        
        # Enhanced confidence if pattern occurs at zone boundary
        if zones and reversal_patterns:
            reversal_patterns = self._enhance_zone_context(reversal_patterns, zones, df['close'].iloc[-1])
        
        # Enhanced confidence if pattern aligns with trend reversal expectation
        if trend_data and reversal_patterns:
            reversal_patterns = self._enhance_trend_context(reversal_patterns, trend_data)
        
        return self._compile_pattern_result(reversal_patterns, 'REVERSAL_PATTERNS')
    
    def _continuation_patterns(self, df: pd.DataFrame, zones: Dict = None, trend_data: Dict = None) -> Dict:
        """
        Focus on trend continuation patterns
        """
        if len(df) < tc.CONTINUATION_PATTERN_LOOKBACK:
            return self._no_signal()
        
        recent_candles = df.tail(tc.CONTINUATION_PATTERN_LOOKBACK)
        
        continuation_patterns = []
        
        # Flag patterns
        flag_patterns = self._detect_flag_patterns(recent_candles)
        continuation_patterns.extend(flag_patterns)
        
        # Pennant patterns
        pennant_patterns = self._detect_pennant_patterns(recent_candles)
        continuation_patterns.extend(pennant_patterns)
        
        # Inside bar continuation
        inside_bar_patterns = self._detect_inside_bar_continuation(recent_candles)
        continuation_patterns.extend(inside_bar_patterns)
        
        # Breakout patterns
        breakout_patterns = self._detect_breakout_patterns(recent_candles)
        continuation_patterns.extend(breakout_patterns)
        
        return self._compile_pattern_result(continuation_patterns, 'CONTINUATION_PATTERNS')
    
    def _momentum_patterns(self, df: pd.DataFrame, zones: Dict = None, trend_data: Dict = None) -> Dict:
        """
        Focus on momentum and strength patterns
        """
        if len(df) < tc.MOMENTUM_PATTERN_LOOKBACK:
            return self._no_signal()
        
        recent_candles = df.tail(tc.MOMENTUM_PATTERN_LOOKBACK)
        
        momentum_patterns = []
        
        # Strong close patterns
        strong_close_patterns = self._detect_strong_close_patterns(recent_candles)
        momentum_patterns.extend(strong_close_patterns)
        
        # Gap patterns
        gap_patterns = self._detect_gap_patterns(recent_candles)
        momentum_patterns.extend(gap_patterns)
        
        # Volume-confirmed patterns (if volume available)
        if 'volume' in df.columns:
            volume_patterns = self._detect_volume_patterns(recent_candles)
            momentum_patterns.extend(volume_patterns)
        
        # Momentum divergence patterns
        momentum_divergence = self._detect_momentum_divergence(df)
        if momentum_divergence:
            momentum_patterns.append(momentum_divergence)
        
        return self._compile_pattern_result(momentum_patterns, 'MOMENTUM_PATTERNS')
    
    def _confluence_patterns(self, df: pd.DataFrame, zones: Dict = None, trend_data: Dict = None) -> Dict:
        """
        Look for confluence of multiple price action signals
        """
        # Get results from multiple methods
        basic_result = self._basic_candlestick_patterns(df, zones, trend_data)
        reversal_result = self._reversal_patterns(df, zones, trend_data)
        momentum_result = self._momentum_patterns(df, zones, trend_data)
        
        # Combine results
        all_patterns = []
        if basic_result['patterns_found']:
            all_patterns.extend(basic_result['patterns_found'])
        if reversal_result['patterns_found']:
            all_patterns.extend(reversal_result['patterns_found'])
        if momentum_result['patterns_found']:
            all_patterns.extend(momentum_result['patterns_found'])
        
        # Look for confluences
        confluences = self._find_pattern_confluences(all_patterns)
        
        if confluences:
            # Calculate confluence score
            confluence_score = self._calculate_confluence_score(confluences)
            
            # Determine overall signal
            bullish_confluences = [c for c in confluences if c['direction'] == 'BULLISH']
            bearish_confluences = [c for c in confluences if c['direction'] == 'BEARISH']
            
            if len(bullish_confluences) > len(bearish_confluences):
                signal = 'BULLISH'
            elif len(bearish_confluences) > len(bullish_confluences):
                signal = 'BEARISH'
            else:
                signal = 'NEUTRAL'
            
            return {
                'signal': signal,
                'confidence': confluence_score,
                'confluences': confluences,
                'method': 'CONFLUENCE_PATTERNS'
            }
        else:
            return self._compile_pattern_result(all_patterns[:3], 'CONFLUENCE_PATTERNS')  # Show top 3 patterns
    
    def _comprehensive_analysis(self, df: pd.DataFrame, zones: Dict = None, trend_data: Dict = None) -> Dict:
        """
        Comprehensive analysis combining all methods
        """
        results = {}
        
        # Run all analysis methods
        for method_name, method_func in self.pattern_methods.items():
            if method_name != 'COMPREHENSIVE':  # Avoid recursion
                try:
                    results[method_name] = method_func(df, zones, trend_data)
                except Exception as e:
                    print(f"Error in {method_name}: {e}")
                    results[method_name] = self._no_signal()
        
        # Combine results intelligently
        combined_analysis = self._combine_analysis_results(results)
        combined_analysis['method'] = 'COMPREHENSIVE'
        
        return combined_analysis
    
    # Pattern detection methods
    def _detect_single_candle_patterns(self, candle: pd.Series) -> List[Dict]:
        """Detect single candlestick patterns"""
        patterns = []
        
        body_size = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']
        upper_wick = candle['high'] - max(candle['open'], candle['close'])
        lower_wick = min(candle['open'], candle['close']) - candle['low']
        
        if total_range == 0:
            return patterns
        
        # Doji pattern
        if body_size < total_range * tc.DOJI_BODY_RATIO:
            patterns.append({
                'name': 'Doji',
                'direction': 'NEUTRAL',
                'confidence': 40,
                'description': 'Indecision candle'
            })
        
        # Hammer pattern
        if (lower_wick > body_size * tc.HAMMER_WICK_RATIO and 
            upper_wick < body_size * tc.HAMMER_UPPER_WICK_RATIO):
            patterns.append({
                'name': 'Hammer',
                'direction': 'BULLISH',
                'confidence': 60,
                'description': 'Potential reversal from support'
            })
        
        # Shooting star pattern
        if (upper_wick > body_size * tc.SHOOTING_STAR_WICK_RATIO and 
            lower_wick < body_size * tc.SHOOTING_STAR_LOWER_WICK_RATIO):
            patterns.append({
                'name': 'Shooting Star',
                'direction': 'BEARISH',
                'confidence': 60,
                'description': 'Potential reversal from resistance'
            })
        
        # Marubozu pattern (strong momentum)
        if body_size > total_range * tc.MARUBOZU_BODY_RATIO:
            direction = 'BULLISH' if candle['close'] > candle['open'] else 'BEARISH'
            patterns.append({
                'name': 'Marubozu',
                'direction': direction,
                'confidence': 70,
                'description': 'Strong momentum candle'
            })
        
        return patterns
    
    def _detect_double_candle_patterns(self, prev_candle: pd.Series, current_candle: pd.Series) -> List[Dict]:
        """Detect two-candle patterns"""
        patterns = []
        
        prev_body = abs(prev_candle['close'] - prev_candle['open'])
        current_body = abs(current_candle['close'] - current_candle['open'])
        
        # Bullish Engulfing
        if (prev_candle['close'] < prev_candle['open'] and  # Previous bearish
            current_candle['close'] > current_candle['open'] and  # Current bullish
            current_candle['open'] < prev_candle['close'] and  # Opens below prev close
            current_candle['close'] > prev_candle['open'] and  # Closes above prev open
            current_body > prev_body * tc.ENGULFING_SIZE_RATIO):  # Significantly larger
            
            patterns.append({
                'name': 'Bullish Engulfing',
                'direction': 'BULLISH',
                'confidence': 75,
                'description': 'Strong bullish reversal pattern'
            })
        
        # Bearish Engulfing
        if (prev_candle['close'] > prev_candle['open'] and  # Previous bullish
            current_candle['close'] < current_candle['open'] and  # Current bearish
            current_candle['open'] > prev_candle['close'] and  # Opens above prev close
            current_candle['close'] < prev_candle['open'] and  # Closes below prev open
            current_body > prev_body * tc.ENGULFING_SIZE_RATIO):  # Significantly larger
            
            patterns.append({
                'name': 'Bearish Engulfing',
                'direction': 'BEARISH',
                'confidence': 75,
                'description': 'Strong bearish reversal pattern'
            })
        
        return patterns
    
    def _detect_pin_bars(self, df: pd.DataFrame) -> List[Dict]:
        """Detect pin bar patterns"""
        patterns = []
        
        if len(df) < 1:
            return patterns
        
        latest = df.iloc[-1]
        body_size = abs(latest['close'] - latest['open'])
        total_range = latest['high'] - latest['low']
        upper_wick = latest['high'] - max(latest['open'], latest['close'])
        lower_wick = min(latest['open'], latest['close']) - latest['low']
        
        if total_range == 0:
            return patterns
        
        # Bullish Pin Bar (rejection from support)
        if (lower_wick > total_range * tc.PIN_BAR_WICK_RATIO and
            upper_wick < total_range * tc.PIN_BAR_OPPOSITE_WICK_RATIO and
            body_size < total_range * tc.PIN_BAR_BODY_RATIO):
            
            patterns.append({
                'name': 'Bullish Pin Bar',
                'direction': 'BULLISH',
                'confidence': 80,
                'description': 'Strong rejection from support level',
                'wick_ratio': lower_wick / total_range
            })
        
        # Bearish Pin Bar (rejection from resistance)
        if (upper_wick > total_range * tc.PIN_BAR_WICK_RATIO and
            lower_wick < total_range * tc.PIN_BAR_OPPOSITE_WICK_RATIO and
            body_size < total_range * tc.PIN_BAR_BODY_RATIO):
            
            patterns.append({
                'name': 'Bearish Pin Bar',
                'direction': 'BEARISH',
                'confidence': 80,
                'description': 'Strong rejection from resistance level',
                'wick_ratio': upper_wick / total_range
            })
        
        return patterns
    
    def _detect_engulfing_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Detect engulfing patterns in recent candles"""
        patterns = []
        
        if len(df) < 2:
            return patterns
        
        # Check last few candle pairs for engulfing
        for i in range(len(df) - 1):
            prev_candle = df.iloc[i]
            current_candle = df.iloc[i + 1]
            
            engulfing_patterns = self._detect_double_candle_patterns(prev_candle, current_candle)
            engulfing_only = [p for p in engulfing_patterns if 'Engulfing' in p['name']]
            patterns.extend(engulfing_only)
        
        return patterns
    
    def _detect_hammer_doji_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Detect hammer and doji patterns"""
        patterns = []
        
        for _, candle in df.iterrows():
            single_patterns = self._detect_single_candle_patterns(candle)
            hammer_doji = [p for p in single_patterns if p['name'] in ['Hammer', 'Doji', 'Shooting Star']]
            patterns.extend(hammer_doji)
        
        return patterns
    
    def _detect_star_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Detect morning/evening star patterns"""
        patterns = []
        
        if len(df) < 3:
            return patterns
        
        # Check for 3-candle star patterns
        for i in range(len(df) - 2):
            candle1 = df.iloc[i]
            candle2 = df.iloc[i + 1]  # Star candle
            candle3 = df.iloc[i + 2]
            
            # Morning Star pattern
            if (candle1['close'] < candle1['open'] and  # First bearish
                abs(candle2['close'] - candle2['open']) < (candle2['high'] - candle2['low']) * tc.STAR_BODY_RATIO and  # Small body star
                candle3['close'] > candle3['open'] and  # Third bullish
                candle3['close'] > (candle1['open'] + candle1['close']) / 2):  # Third closes above midpoint of first
                
                patterns.append({
                    'name': 'Morning Star',
                    'direction': 'BULLISH',
                    'confidence': 85,
                    'description': 'Strong bullish reversal pattern'
                })
            
            # Evening Star pattern
            if (candle1['close'] > candle1['open'] and  # First bullish
                abs(candle2['close'] - candle2['open']) < (candle2['high'] - candle2['low']) * tc.STAR_BODY_RATIO and  # Small body star
                candle3['close'] < candle3['open'] and  # Third bearish
                candle3['close'] < (candle1['open'] + candle1['close']) / 2):  # Third closes below midpoint of first
                
                patterns.append({
                    'name': 'Evening Star',
                    'direction': 'BEARISH',
                    'confidence': 85,
                    'description': 'Strong bearish reversal pattern'
                })
        
        return patterns
    
    # Continuation pattern methods (simplified implementations)
    def _detect_flag_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Detect flag continuation patterns"""
        # Simplified flag detection
        patterns = []
        
        if len(df) < tc.FLAG_PATTERN_MIN_CANDLES:
            return patterns
        
        # Look for consolidation after strong move
        recent_range = df['high'].max() - df['low'].min()
        recent_bodies = abs(df['close'] - df['open']).mean()
        
        if recent_bodies < recent_range * tc.FLAG_CONSOLIDATION_RATIO:
            # Determine flag direction based on overall trend
            start_price = df['close'].iloc[0]
            end_price = df['close'].iloc[-1]
            
            if end_price > start_price * (1 + tc.FLAG_TREND_THRESHOLD):
                direction = 'BULLISH'
            elif end_price < start_price * (1 - tc.FLAG_TREND_THRESHOLD):
                direction = 'BEARISH'
            else:
                return patterns  # No clear trend
            
            patterns.append({
                'name': 'Flag Pattern',
                'direction': direction,
                'confidence': 65,
                'description': f'{direction.lower().capitalize()} flag continuation pattern'
            })
        
        return patterns
    
    def _detect_pennant_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Detect pennant continuation patterns"""
        # Similar to flag but with converging price action
        return []  # Simplified - not implemented in detail
    
    def _detect_inside_bar_continuation(self, df: pd.DataFrame) -> List[Dict]:
        """Detect inside bar continuation patterns"""
        patterns = []
        
        if len(df) < 2:
            return patterns
        
        prev_candle = df.iloc[-2]
        current_candle = df.iloc[-1]
        
        # Inside bar: current candle's range is within previous candle's range
        if (current_candle['high'] <= prev_candle['high'] and
            current_candle['low'] >= prev_candle['low']):
            
            patterns.append({
                'name': 'Inside Bar',
                'direction': 'CONTINUATION',
                'confidence': 50,
                'description': 'Consolidation pattern - breakout expected'
            })
        
        return patterns
    
    def _detect_breakout_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Detect breakout patterns"""
        patterns = []
        
        if len(df) < tc.BREAKOUT_LOOKBACK:
            return patterns
        
        recent_high = df['high'].tail(tc.BREAKOUT_LOOKBACK - 1).max()
        recent_low = df['low'].tail(tc.BREAKOUT_LOOKBACK - 1).min()
        current_high = df['high'].iloc[-1]
        current_low = df['low'].iloc[-1]
        
        # Bullish breakout
        if current_high > recent_high * (1 + tc.BREAKOUT_THRESHOLD):
            patterns.append({
                'name': 'Bullish Breakout',
                'direction': 'BULLISH',
                'confidence': 70,
                'description': 'Breakout above recent resistance'
            })
        
        # Bearish breakdown
        if current_low < recent_low * (1 - tc.BREAKOUT_THRESHOLD):
            patterns.append({
                'name': 'Bearish Breakdown',
                'direction': 'BEARISH',
                'confidence': 70,
                'description': 'Breakdown below recent support'
            })
        
        return patterns
    
    def _detect_strong_close_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Detect strong close patterns indicating momentum"""
        patterns = []
        
        latest = df.iloc[-1]
        total_range = latest['high'] - latest['low']
        
        if total_range == 0:
            return patterns
        
        close_position = (latest['close'] - latest['low']) / total_range
        
        # Strong bullish close (close near high)
        if close_position > tc.STRONG_CLOSE_THRESHOLD:
            patterns.append({
                'name': 'Strong Bullish Close',
                'direction': 'BULLISH',
                'confidence': 60,
                'description': f'Close in top {(1-tc.STRONG_CLOSE_THRESHOLD)*100:.0f}% of range',
                'close_position': close_position
            })
        
        # Strong bearish close (close near low)
        elif close_position < (1 - tc.STRONG_CLOSE_THRESHOLD):
            patterns.append({
                'name': 'Strong Bearish Close',
                'direction': 'BEARISH',
                'confidence': 60,
                'description': f'Close in bottom {(1-tc.STRONG_CLOSE_THRESHOLD)*100:.0f}% of range',
                'close_position': close_position
            })
        
        return patterns
    
    def _detect_gap_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Detect gap patterns"""
        patterns = []
        
        if len(df) < 2:
            return patterns
        
        prev_candle = df.iloc[-2]
        current_candle = df.iloc[-1]
        
        # Gap up
        if current_candle['low'] > prev_candle['high']:
            gap_size = (current_candle['low'] - prev_candle['high']) / prev_candle['close']
            if gap_size > tc.MIN_GAP_SIZE:
                patterns.append({
                    'name': 'Gap Up',
                    'direction': 'BULLISH',
                    'confidence': 65,
                    'description': f'Bullish gap of {gap_size*100:.1f}%',
                    'gap_size': gap_size
                })
        
        # Gap down
        elif current_candle['high'] < prev_candle['low']:
            gap_size = (prev_candle['low'] - current_candle['high']) / prev_candle['close']
            if gap_size > tc.MIN_GAP_SIZE:
                patterns.append({
                    'name': 'Gap Down',
                    'direction': 'BEARISH',
                    'confidence': 65,
                    'description': f'Bearish gap of {gap_size*100:.1f}%',
                    'gap_size': gap_size
                })
        
        return patterns
    
    def _detect_volume_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Detect volume-confirmed patterns"""
        patterns = []
        
        if 'volume' not in df.columns or len(df) < tc.VOLUME_PATTERN_LOOKBACK:
            return patterns
        
        latest_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].tail(tc.VOLUME_PATTERN_LOOKBACK).mean()
        
        if latest_volume > avg_volume * tc.HIGH_VOLUME_MULTIPLIER:
            patterns.append({
                'name': 'High Volume Confirmation',
                'direction': 'CONFIRMATION',
                'confidence': 25,  # Adds to other patterns
                'description': f'Volume {latest_volume/avg_volume:.1f}x above average',
                'volume_ratio': latest_volume / avg_volume
            })
        
        return patterns
    
    def _detect_momentum_divergence(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect momentum divergence patterns"""
        if len(df) < tc.DIVERGENCE_LOOKBACK:
            return None
        
        # Simplified momentum divergence detection
        # This would typically use RSI or other momentum indicators
        recent_prices = df['close'].tail(tc.DIVERGENCE_LOOKBACK)
        
        # Simple price momentum
        price_momentum = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
        
        if abs(price_momentum) > tc.MOMENTUM_DIVERGENCE_THRESHOLD:
            direction = 'BULLISH' if price_momentum > 0 else 'BEARISH'
            return {
                'name': 'Momentum Pattern',
                'direction': direction,
                'confidence': 55,
                'description': f'{direction.lower().capitalize()} momentum detected',
                'momentum': price_momentum
            }
        
        return None
    
    # Helper methods
    def _enhance_zone_context(self, patterns: List[Dict], zones: Dict, current_price: float) -> List[Dict]:
        """Enhance pattern confidence based on zone context"""
        enhanced_patterns = []
        
        for pattern in patterns:
            enhanced_pattern = pattern.copy()
            
            # Check if price is near a zone
            for zone_name, zone_data in zones.items():
                if self._is_price_near_zone(current_price, zone_data):
                    # Increase confidence for reversal patterns at zones
                    if pattern['direction'] in ['BULLISH', 'BEARISH']:
                        enhanced_pattern['confidence'] += tc.ZONE_CONTEXT_BONUS
                        enhanced_pattern['zone_context'] = f"Pattern at {zone_name}"
                    break
            
            enhanced_patterns.append(enhanced_pattern)
        
        return enhanced_patterns
    
    def _enhance_trend_context(self, patterns: List[Dict], trend_data: Dict) -> List[Dict]:
        """Enhance pattern confidence based on trend context"""
        enhanced_patterns = []
        
        trend_bias = trend_data.get('bias', 'NEUTRAL')
        
        for pattern in patterns:
            enhanced_pattern = pattern.copy()
            
            # Boost patterns aligned with trend
            if ((pattern['direction'] == 'BULLISH' and trend_bias == 'BULLISH') or
                (pattern['direction'] == 'BEARISH' and trend_bias == 'BEARISH')):
                enhanced_pattern['confidence'] += tc.TREND_ALIGNMENT_BONUS
                enhanced_pattern['trend_alignment'] = True
            else:
                enhanced_pattern['trend_alignment'] = False
            
            enhanced_patterns.append(enhanced_pattern)
        
        return enhanced_patterns
    
    def _is_price_near_zone(self, price: float, zone_data: Dict) -> bool:
        """Check if price is near a zone boundary"""
        zone_height = zone_data['upper'] - zone_data['lower']
        proximity_threshold = zone_height * tc.ZONE_PROXIMITY_RATIO
        
        return (abs(price - zone_data['upper']) <= proximity_threshold or
                abs(price - zone_data['lower']) <= proximity_threshold or
                (zone_data['lower'] <= price <= zone_data['upper']))
    
    def _find_pattern_confluences(self, patterns: List[Dict]) -> List[Dict]:
        """Find confluences between patterns"""
        confluences = []
        
        # Group patterns by direction
        bullish_patterns = [p for p in patterns if p['direction'] == 'BULLISH']
        bearish_patterns = [p for p in patterns if p['direction'] == 'BEARISH']
        
        # Create confluences for each direction if multiple patterns exist
        if len(bullish_patterns) >= tc.MIN_CONFLUENCE_PATTERNS:
            confluences.append({
                'direction': 'BULLISH',
                'patterns': bullish_patterns,
                'pattern_count': len(bullish_patterns),
                'combined_confidence': min(sum(p['confidence'] for p in bullish_patterns), 100)
            })
        
        if len(bearish_patterns) >= tc.MIN_CONFLUENCE_PATTERNS:
            confluences.append({
                'direction': 'BEARISH',
                'patterns': bearish_patterns,
                'pattern_count': len(bearish_patterns),
                'combined_confidence': min(sum(p['confidence'] for p in bearish_patterns), 100)
            })
        
        return confluences
    
    def _calculate_confluence_score(self, confluences: List[Dict]) -> int:
        """Calculate overall confluence score"""
        if not confluences:
            return 0
        
        # Use the highest confidence confluence
        max_confidence = max(c['combined_confidence'] for c in confluences)
        
        # Bonus for multiple confluences
        confluence_bonus = (len(confluences) - 1) * tc.MULTIPLE_CONFLUENCE_BONUS
        
        return min(max_confidence + confluence_bonus, 100)
    
    def _compile_pattern_result(self, patterns: List[Dict], method: str) -> Dict:
        """Compile pattern results into standard format"""
        if not patterns:
            return self._no_signal()
        
        # Calculate overall signal and confidence
        bullish_patterns = [p for p in patterns if p['direction'] == 'BULLISH']
        bearish_patterns = [p for p in patterns if p['direction'] == 'BEARISH']
        
        if len(bullish_patterns) > len(bearish_patterns):
            signal = 'BULLISH'
            confidence = min(sum(p['confidence'] for p in bullish_patterns), 100)
        elif len(bearish_patterns) > len(bullish_patterns):
            signal = 'BEARISH'
            confidence = min(sum(p['confidence'] for p in bearish_patterns), 100)
        else:
            signal = 'NEUTRAL'
            confidence = 40
        
        return {
            'signal': signal,
            'confidence': confidence,
            'patterns_found': patterns,
            'pattern_count': len(patterns),
            'method': method
        }
    
    def _combine_analysis_results(self, results: Dict) -> Dict:
        """Combine results from multiple analysis methods"""
        all_patterns = []
        
        # Collect all patterns
        for method_result in results.values():
            if method_result.get('patterns_found'):
                all_patterns.extend(method_result['patterns_found'])
        
        # Find the strongest signals
        if all_patterns:
            return self._compile_pattern_result(all_patterns, 'COMPREHENSIVE')
        else:
            return self._no_signal()
    
    def _no_signal(self) -> Dict:
        """Return no signal result"""
        return {
            'signal': 'NO_SIGNAL',
            'confidence': 0,
            'patterns_found': [],
            'pattern_count': 0
        }

# Configuration class
class PriceActionConfig:
    """Configuration for price action confirmation"""
    
    METHODS = {
        'BASIC_PATTERNS': 'Basic candlestick patterns',
        'REVERSAL_PATTERNS': 'Focus on reversal patterns',
        'CONTINUATION_PATTERNS': 'Focus on continuation patterns',
        'MOMENTUM_PATTERNS': 'Focus on momentum patterns',
        'CONFLUENCE_PATTERNS': 'Multiple pattern confluence',
        'COMPREHENSIVE': 'All pattern types (recommended)'
    }
    
    @staticmethod
    def get_method_description(method: str) -> str:
        return PriceActionConfig.METHODS.get(method, 'Unknown method')