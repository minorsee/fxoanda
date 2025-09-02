"""
Enhanced Entry Timing Module
Modular system for better entry timing and zone rejection detection
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trading_config as tc

class EntryTiming:
    """
    Modular entry timing system focused on zone rejection and confirmation
    """
    
    def __init__(self):
        self.entry_methods = {
            'IMMEDIATE': self._immediate_entry,
            'ZONE_REJECTION': self._zone_rejection_entry,
            'PULLBACK_COMPLETION': self._pullback_completion_entry,
            'BREAKOUT_RETEST': self._breakout_retest_entry,
            'CONFLUENCE_CONFIRMATION': self._confluence_confirmation_entry
        }
    
    def get_entry_signal(self, df: pd.DataFrame, zones: Dict, 
                        method: str = tc.ENTRY_TIMING_METHOD) -> Dict:
        """
        Main entry point - returns entry signal based on selected method
        
        Args:
            df: OHLCV dataframe
            zones: Dictionary of trading zones
            method: Entry timing method to use
            
        Returns:
            Dict with signal, confidence, and entry details
        """
        if method not in self.entry_methods:
            raise ValueError(f"Unknown entry method: {method}")
        
        return self.entry_methods[method](df, zones)
    
    def _immediate_entry(self, df: pd.DataFrame, zones: Dict) -> Dict:
        """
        Original method - enter immediately when price is in zone
        """
        current_price = df['close'].iloc[-1]
        
        for zone_name, zone_data in zones.items():
            if self._is_price_in_zone(current_price, zone_data):
                return {
                    'signal': 'ENTRY',
                    'method': 'IMMEDIATE',
                    'confidence': 30,  # Low confidence for immediate entry
                    'zone': zone_name,
                    'reason': f'Price in {zone_name}'
                }
        
        return {'signal': 'NO_ENTRY', 'method': 'IMMEDIATE', 'confidence': 0}
    
    def _zone_rejection_entry(self, df: pd.DataFrame, zones: Dict) -> Dict:
        """
        Wait for zone rejection before entering
        Higher probability entries with better risk/reward
        """
        if len(df) < 3:
            return {'signal': 'NO_ENTRY', 'method': 'ZONE_REJECTION', 'confidence': 0}
        
        latest_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]
        
        for zone_name, zone_data in zones.items():
            rejection_signal = self._detect_zone_rejection(latest_candle, prev_candle, zone_data)
            
            if rejection_signal['detected']:
                confidence = self._calculate_rejection_confidence(
                    latest_candle, zone_data, rejection_signal
                )
                
                return {
                    'signal': 'ENTRY',
                    'method': 'ZONE_REJECTION',
                    'confidence': confidence,
                    'zone': zone_name,
                    'direction': rejection_signal['direction'],
                    'reason': f'Zone rejection from {zone_name}',
                    'rejection_details': rejection_signal
                }
        
        return {'signal': 'NO_ENTRY', 'method': 'ZONE_REJECTION', 'confidence': 0}
    
    def _pullback_completion_entry(self, df: pd.DataFrame, zones: Dict) -> Dict:
        """
        Enter after pullback completion within zone
        """
        if len(df) < tc.PULLBACK_LOOKBACK:
            return {'signal': 'NO_ENTRY', 'method': 'PULLBACK_COMPLETION', 'confidence': 0}
        
        recent_data = df.tail(tc.PULLBACK_LOOKBACK)
        pullback_analysis = self._analyze_pullback(recent_data)
        
        if pullback_analysis['completed']:
            for zone_name, zone_data in zones.items():
                if self._is_pullback_in_zone(pullback_analysis, zone_data):
                    confidence = self._calculate_pullback_confidence(pullback_analysis)
                    
                    return {
                        'signal': 'ENTRY',
                        'method': 'PULLBACK_COMPLETION',
                        'confidence': confidence,
                        'zone': zone_name,
                        'direction': pullback_analysis['direction'],
                        'reason': f'Pullback completion in {zone_name}',
                        'pullback_details': pullback_analysis
                    }
        
        return {'signal': 'NO_ENTRY', 'method': 'PULLBACK_COMPLETION', 'confidence': 0}
    
    def _breakout_retest_entry(self, df: pd.DataFrame, zones: Dict) -> Dict:
        """
        Enter on breakout retest of zones
        """
        if len(df) < tc.BREAKOUT_LOOKBACK:
            return {'signal': 'NO_ENTRY', 'method': 'BREAKOUT_RETEST', 'confidence': 0}
        
        breakout_analysis = self._detect_breakout_retest(df, zones)
        
        if breakout_analysis['detected']:
            return {
                'signal': 'ENTRY',
                'method': 'BREAKOUT_RETEST',
                'confidence': breakout_analysis['confidence'],
                'zone': breakout_analysis['zone'],
                'direction': breakout_analysis['direction'],
                'reason': f'Breakout retest of {breakout_analysis["zone"]}',
                'breakout_details': breakout_analysis
            }
        
        return {'signal': 'NO_ENTRY', 'method': 'BREAKOUT_RETEST', 'confidence': 0}
    
    def _confluence_confirmation_entry(self, df: pd.DataFrame, zones: Dict) -> Dict:
        """
        Enter only with multiple confirmations
        """
        confirmations = []
        
        # Check for multiple entry signals
        zone_rejection = self._zone_rejection_entry(df, zones)
        if zone_rejection['signal'] == 'ENTRY':
            confirmations.append(('zone_rejection', zone_rejection['confidence']))
        
        pullback_completion = self._pullback_completion_entry(df, zones)
        if pullback_completion['signal'] == 'ENTRY':
            confirmations.append(('pullback_completion', pullback_completion['confidence']))
        
        # Volume confirmation
        if self._has_volume_confirmation(df):
            confirmations.append(('volume', 15))
        
        # Price action confirmation
        if self._has_price_action_confirmation(df):
            confirmations.append(('price_action', 20))
        
        if len(confirmations) >= tc.MIN_CONFLUENCE_CONFIRMATIONS:
            total_confidence = min(sum(conf for _, conf in confirmations), 95)
            
            return {
                'signal': 'ENTRY',
                'method': 'CONFLUENCE_CONFIRMATION',
                'confidence': total_confidence,
                'confirmations': confirmations,
                'reason': f'{len(confirmations)} confluences detected'
            }
        
        return {'signal': 'NO_ENTRY', 'method': 'CONFLUENCE_CONFIRMATION', 'confidence': 0}
    
    def _detect_zone_rejection(self, latest_candle: pd.Series, prev_candle: pd.Series, 
                              zone_data: Dict) -> Dict:
        """
        Detect zone rejection patterns
        """
        # Bullish rejection from support zone
        if (latest_candle['low'] <= zone_data['lower'] and 
            latest_candle['close'] > zone_data['center']):
            
            # Check for strong wick rejection
            body_size = abs(latest_candle['close'] - latest_candle['open'])
            lower_wick = latest_candle['open'] - latest_candle['low'] if latest_candle['close'] > latest_candle['open'] else latest_candle['close'] - latest_candle['low']
            
            if lower_wick > body_size * tc.WICK_REJECTION_RATIO:
                return {
                    'detected': True,
                    'direction': 'BULLISH',
                    'type': 'SUPPORT_REJECTION',
                    'wick_strength': lower_wick / body_size if body_size > 0 else 5.0,
                    'bounce_distance': latest_candle['close'] - latest_candle['low']
                }
        
        # Bearish rejection from resistance zone
        if (latest_candle['high'] >= zone_data['upper'] and 
            latest_candle['close'] < zone_data['center']):
            
            body_size = abs(latest_candle['close'] - latest_candle['open'])
            upper_wick = latest_candle['high'] - latest_candle['open'] if latest_candle['close'] < latest_candle['open'] else latest_candle['high'] - latest_candle['close']
            
            if upper_wick > body_size * tc.WICK_REJECTION_RATIO:
                return {
                    'detected': True,
                    'direction': 'BEARISH',
                    'type': 'RESISTANCE_REJECTION',
                    'wick_strength': upper_wick / body_size if body_size > 0 else 5.0,
                    'bounce_distance': latest_candle['high'] - latest_candle['close']
                }
        
        return {'detected': False}
    
    def _calculate_rejection_confidence(self, candle: pd.Series, zone_data: Dict, 
                                       rejection_signal: Dict) -> int:
        """
        Calculate confidence based on rejection strength
        """
        base_confidence = 45
        
        # Wick strength bonus
        wick_bonus = min(rejection_signal['wick_strength'] * 10, 30)
        base_confidence += wick_bonus
        
        # Bounce distance bonus
        zone_height = zone_data['upper'] - zone_data['lower']
        bounce_ratio = rejection_signal['bounce_distance'] / zone_height
        bounce_bonus = min(bounce_ratio * 20, 20)
        base_confidence += bounce_bonus
        
        return min(int(base_confidence), 95)
    
    def _analyze_pullback(self, df: pd.DataFrame) -> Dict:
        """
        Analyze if pullback is complete
        """
        if len(df) < 3:
            return {'completed': False}
        
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        # Simple pullback detection
        recent_trend = 'BULLISH' if closes[-1] > closes[-3] else 'BEARISH'
        
        if recent_trend == 'BULLISH':
            # Look for pullback low and recovery
            pullback_low = min(lows[-3:])
            current_high = highs[-1]
            if closes[-1] > pullback_low and current_high > pullback_low:
                return {
                    'completed': True,
                    'direction': 'BULLISH',
                    'pullback_low': pullback_low,
                    'recovery_strength': (closes[-1] - pullback_low) / pullback_low
                }
        else:
            # Look for pullback high and continuation down
            pullback_high = max(highs[-3:])
            current_low = lows[-1]
            if closes[-1] < pullback_high and current_low < pullback_high:
                return {
                    'completed': True,
                    'direction': 'BEARISH',
                    'pullback_high': pullback_high,
                    'recovery_strength': (pullback_high - closes[-1]) / pullback_high
                }
        
        return {'completed': False}
    
    def _is_pullback_in_zone(self, pullback_analysis: Dict, zone_data: Dict) -> bool:
        """
        Check if pullback completion happened within zone
        """
        if pullback_analysis['direction'] == 'BULLISH':
            return zone_data['lower'] <= pullback_analysis['pullback_low'] <= zone_data['upper']
        else:
            return zone_data['lower'] <= pullback_analysis['pullback_high'] <= zone_data['upper']
    
    def _calculate_pullback_confidence(self, pullback_analysis: Dict) -> int:
        """
        Calculate confidence based on pullback strength
        """
        base_confidence = 50
        strength_bonus = min(pullback_analysis['recovery_strength'] * 100, 30)
        return min(int(base_confidence + strength_bonus), 85)
    
    def _detect_breakout_retest(self, df: pd.DataFrame, zones: Dict) -> Dict:
        """
        Detect breakout and retest patterns
        """
        # Implementation for breakout retest detection
        # This is a complex pattern - simplified version
        return {'detected': False}
    
    def _has_volume_confirmation(self, df: pd.DataFrame) -> bool:
        """
        Check for volume confirmation
        """
        if 'volume' not in df.columns or len(df) < 5:
            return False
        
        recent_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].tail(5).mean()
        
        return recent_volume > avg_volume * tc.VOLUME_CONFIRMATION_MULTIPLIER
    
    def _has_price_action_confirmation(self, df: pd.DataFrame) -> bool:
        """
        Check for basic price action confirmation
        """
        if len(df) < 2:
            return False
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Strong close near high/low
        body_position = (latest['close'] - latest['low']) / (latest['high'] - latest['low']) if latest['high'] != latest['low'] else 0.5
        
        return body_position > 0.7 or body_position < 0.3
    
    def _is_price_in_zone(self, price: float, zone_data: Dict) -> bool:
        """
        Helper method to check if price is in zone
        """
        return zone_data['lower'] <= price <= zone_data['upper']

# Configuration class for easy plug-and-play
class EntryTimingConfig:
    """
    Configuration for entry timing methods
    """
    METHODS = {
        'IMMEDIATE': 'Enter immediately when price is in zone (original)',
        'ZONE_REJECTION': 'Wait for zone rejection confirmation (recommended)',
        'PULLBACK_COMPLETION': 'Enter after pullback completion',
        'BREAKOUT_RETEST': 'Enter on breakout retest',
        'CONFLUENCE_CONFIRMATION': 'Multiple confirmation required'
    }
    
    @staticmethod
    def get_method_description(method: str) -> str:
        return EntryTimingConfig.METHODS.get(method, 'Unknown method')