"""
Dynamic Zone Sizing Module
Adaptive zone sizing based on market conditions, volatility, and trend strength
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trading_config as tc

class DynamicZones:
    """
    Dynamic zone sizing system that adapts to market conditions
    """
    
    def __init__(self):
        self.zone_methods = {
            'FIXED': self._fixed_zones,
            'ATR_BASED': self._atr_based_zones,
            'VOLATILITY_ADAPTIVE': self._volatility_adaptive_zones,
            'TREND_ADAPTIVE': self._trend_adaptive_zones,
            'MARKET_CONDITION': self._market_condition_zones,
            'COMPOSITE_ZONES': self._composite_zones
        }
    
    def create_zones(self, df: pd.DataFrame, 
                    method: str = tc.ZONE_SIZING_METHOD,
                    trend_data: Dict = None) -> Dict:
        """
        Main entry point for dynamic zone creation
        
        Args:
            df: OHLCV dataframe
            method: Zone sizing method to use
            trend_data: Optional trend analysis data
            
        Returns:
            Dict with zone boundaries and metadata
        """
        if method not in self.zone_methods:
            raise ValueError(f"Unknown zone method: {method}")
        
        if df.empty:
            return {}
        
        # Get latest MA values
        latest = df.iloc[-1]
        ma_values = {
            'fast_ma': latest['fast_ma'],
            'slow_ma': latest['slow_ma'],
            'trend_ma': latest['trend_ma']
        }
        
        # Calculate zones using selected method
        zones = self.zone_methods[method](df, ma_values, trend_data)
        
        # Add metadata to each zone
        for zone_name, zone_data in zones.items():
            zones[zone_name].update(self._calculate_zone_metadata(df, zone_data, zone_name))
        
        return zones
    
    def _fixed_zones(self, df: pd.DataFrame, ma_values: Dict, trend_data: Dict = None) -> Dict:
        """
        Original fixed-width zones
        """
        pip_value = 0.0001
        zone_width = tc.ZONE_WIDTH_PIPS * pip_value
        
        zones = {}
        for ma_name, ma_price in ma_values.items():
            zone_name = f"{ma_name}_zone"
            zones[zone_name] = {
                'center': ma_price,
                'upper': ma_price + zone_width,
                'lower': ma_price - zone_width,
                'width_pips': tc.ZONE_WIDTH_PIPS,
                'method': 'FIXED'
            }
        
        return zones
    
    def _atr_based_zones(self, df: pd.DataFrame, ma_values: Dict, trend_data: Dict = None) -> Dict:
        """
        Zones sized based on Average True Range (volatility)
        """
        if len(df) < 14:
            return self._fixed_zones(df, ma_values, trend_data)
        
        # Calculate ATR
        atr = self._calculate_atr(df, tc.ATR_PERIOD)
        latest_atr = atr.iloc[-1]
        
        # Zone width as multiple of ATR
        zone_width = latest_atr * tc.ATR_ZONE_MULTIPLIER
        zone_width_pips = zone_width / 0.0001
        
        zones = {}
        for ma_name, ma_price in ma_values.items():
            zone_name = f"{ma_name}_zone"
            zones[zone_name] = {
                'center': ma_price,
                'upper': ma_price + zone_width,
                'lower': ma_price - zone_width,
                'width_pips': zone_width_pips,
                'atr': latest_atr,
                'method': 'ATR_BASED'
            }
        
        return zones
    
    def _volatility_adaptive_zones(self, df: pd.DataFrame, ma_values: Dict, trend_data: Dict = None) -> Dict:
        """
        Zones that adapt to recent volatility changes
        """
        if len(df) < tc.VOLATILITY_LOOKBACK:
            return self._atr_based_zones(df, ma_values, trend_data)
        
        # Calculate volatility metrics
        volatility_data = self._calculate_volatility_metrics(df)
        
        # Determine volatility regime
        volatility_regime = self._classify_volatility_regime(volatility_data)
        
        # Adjust zone width based on volatility
        base_atr = volatility_data['current_atr']
        
        if volatility_regime == 'HIGH_VOLATILITY':
            zone_multiplier = tc.HIGH_VOLATILITY_MULTIPLIER
        elif volatility_regime == 'LOW_VOLATILITY':
            zone_multiplier = tc.LOW_VOLATILITY_MULTIPLIER
        else:  # NORMAL_VOLATILITY
            zone_multiplier = tc.NORMAL_VOLATILITY_MULTIPLIER
        
        zone_width = base_atr * zone_multiplier
        zone_width_pips = zone_width / 0.0001
        
        zones = {}
        for ma_name, ma_price in ma_values.items():
            zone_name = f"{ma_name}_zone"
            zones[zone_name] = {
                'center': ma_price,
                'upper': ma_price + zone_width,
                'lower': ma_price - zone_width,
                'width_pips': zone_width_pips,
                'volatility_regime': volatility_regime,
                'volatility_data': volatility_data,
                'method': 'VOLATILITY_ADAPTIVE'
            }
        
        return zones
    
    def _trend_adaptive_zones(self, df: pd.DataFrame, ma_values: Dict, trend_data: Dict = None) -> Dict:
        """
        Zones that adapt based on trend strength and direction
        """
        # Start with ATR-based zones
        zones = self._atr_based_zones(df, ma_values, trend_data)
        
        if not trend_data:
            return zones
        
        # Adjust based on trend strength
        trend_strength = trend_data.get('strength', 'WEAK')
        trend_bias = trend_data.get('bias', 'NEUTRAL')
        
        # Trend strength multipliers
        strength_multipliers = {
            'STRONG': tc.STRONG_TREND_ZONE_MULTIPLIER,
            'MEDIUM': tc.MEDIUM_TREND_ZONE_MULTIPLIER,
            'WEAK': tc.WEAK_TREND_ZONE_MULTIPLIER
        }
        
        multiplier = strength_multipliers.get(trend_strength, 1.0)
        
        # Adjust zones
        for zone_name, zone_data in zones.items():
            original_width = zone_data['upper'] - zone_data['center']
            new_width = original_width * multiplier
            
            zones[zone_name].update({
                'upper': zone_data['center'] + new_width,
                'lower': zone_data['center'] - new_width,
                'width_pips': new_width / 0.0001,
                'trend_multiplier': multiplier,
                'trend_strength': trend_strength,
                'trend_bias': trend_bias,
                'method': 'TREND_ADAPTIVE'
            })
        
        return zones
    
    def _market_condition_zones(self, df: pd.DataFrame, ma_values: Dict, trend_data: Dict = None) -> Dict:
        """
        Zones adapted to overall market conditions (ranging vs trending)
        """
        if len(df) < tc.MARKET_CONDITION_LOOKBACK:
            return self._trend_adaptive_zones(df, ma_values, trend_data)
        
        # Determine market condition
        market_condition = self._classify_market_condition(df)
        
        # Start with base zones
        zones = self._atr_based_zones(df, ma_values, trend_data)
        
        # Adjust based on market condition
        if market_condition['type'] == 'TRENDING':
            # Narrower zones in trending markets
            multiplier = tc.TRENDING_MARKET_MULTIPLIER
        elif market_condition['type'] == 'RANGING':
            # Wider zones in ranging markets
            multiplier = tc.RANGING_MARKET_MULTIPLIER
        else:  # MIXED
            multiplier = tc.MIXED_MARKET_MULTIPLIER
        
        # Apply adjustments
        for zone_name, zone_data in zones.items():
            original_width = zone_data['upper'] - zone_data['center']
            new_width = original_width * multiplier
            
            zones[zone_name].update({
                'upper': zone_data['center'] + new_width,
                'lower': zone_data['center'] - new_width,
                'width_pips': new_width / 0.0001,
                'market_condition': market_condition,
                'condition_multiplier': multiplier,
                'method': 'MARKET_CONDITION'
            })
        
        return zones
    
    def _composite_zones(self, df: pd.DataFrame, ma_values: Dict, trend_data: Dict = None) -> Dict:
        """
        Composite zones using multiple factors
        """
        # Calculate all zone types
        atr_zones = self._atr_based_zones(df, ma_values, trend_data)
        volatility_zones = self._volatility_adaptive_zones(df, ma_values, trend_data)
        
        if len(df) >= tc.MARKET_CONDITION_LOOKBACK:
            market_zones = self._market_condition_zones(df, ma_values, trend_data)
        else:
            market_zones = atr_zones
        
        # Combine factors
        zones = {}
        for ma_name, ma_price in ma_values.items():
            zone_name = f"{ma_name}_zone"
            
            # Get widths from different methods
            atr_width = atr_zones[zone_name]['upper'] - atr_zones[zone_name]['center']
            vol_width = volatility_zones[zone_name]['upper'] - volatility_zones[zone_name]['center']
            market_width = market_zones[zone_name]['upper'] - market_zones[zone_name]['center']
            
            # Weight the different methods
            weights = tc.COMPOSITE_ZONE_WEIGHTS
            
            composite_width = (
                atr_width * weights['atr'] +
                vol_width * weights['volatility'] +
                market_width * weights['market_condition']
            ) / sum(weights.values())
            
            zones[zone_name] = {
                'center': ma_price,
                'upper': ma_price + composite_width,
                'lower': ma_price - composite_width,
                'width_pips': composite_width / 0.0001,
                'atr_width': atr_width / 0.0001,
                'volatility_width': vol_width / 0.0001,
                'market_width': market_width / 0.0001,
                'composite_weights': weights,
                'method': 'COMPOSITE_ZONES'
            }
        
        return zones
    
    def _calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(window=period).mean()
    
    def _calculate_volatility_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive volatility metrics"""
        lookback = tc.VOLATILITY_LOOKBACK
        recent_data = df.tail(lookback)
        
        # Current ATR
        atr_series = self._calculate_atr(df, tc.ATR_PERIOD)
        current_atr = atr_series.iloc[-1]
        
        # ATR trend (is volatility increasing or decreasing?)
        atr_recent = atr_series.tail(lookback)
        atr_slope = np.polyfit(range(len(atr_recent)), atr_recent.values, 1)[0]
        
        # Volatility percentile (where is current volatility vs historical?)
        atr_percentile = (current_atr - atr_series.quantile(0.05)) / (atr_series.quantile(0.95) - atr_series.quantile(0.05))
        atr_percentile = max(0, min(1, atr_percentile))  # Clamp between 0-1
        
        # Price range metrics
        recent_high = recent_data['high'].max()
        recent_low = recent_data['low'].min()
        current_price = df['close'].iloc[-1]
        range_position = (current_price - recent_low) / (recent_high - recent_low) if recent_high != recent_low else 0.5
        
        return {
            'current_atr': current_atr,
            'atr_slope': atr_slope,
            'atr_percentile': atr_percentile,
            'recent_high': recent_high,
            'recent_low': recent_low,
            'range_position': range_position,
            'lookback_period': lookback
        }
    
    def _classify_volatility_regime(self, volatility_data: Dict) -> str:
        """Classify current volatility regime"""
        atr_percentile = volatility_data['atr_percentile']
        atr_slope = volatility_data['atr_slope']
        
        # High volatility if in top 20% and increasing
        if atr_percentile > 0.8 or (atr_percentile > 0.6 and atr_slope > 0):
            return 'HIGH_VOLATILITY'
        
        # Low volatility if in bottom 20% and decreasing
        elif atr_percentile < 0.2 or (atr_percentile < 0.4 and atr_slope < 0):
            return 'LOW_VOLATILITY'
        
        else:
            return 'NORMAL_VOLATILITY'
    
    def _classify_market_condition(self, df: pd.DataFrame) -> Dict:
        """Classify market as trending or ranging"""
        lookback = tc.MARKET_CONDITION_LOOKBACK
        recent_data = df.tail(lookback)
        
        # Calculate price movement efficiency
        total_price_move = abs(recent_data['close'].iloc[-1] - recent_data['close'].iloc[0])
        total_path_length = sum(abs(recent_data['close'].diff().dropna()))
        
        efficiency = total_price_move / total_path_length if total_path_length > 0 else 0
        
        # Calculate trend strength using linear regression
        x = np.arange(len(recent_data))
        y = recent_data['close'].values
        slope, intercept = np.polyfit(x, y, 1)
        
        # R-squared for trend quality
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Classify based on efficiency and r-squared
        if efficiency > tc.TRENDING_EFFICIENCY_THRESHOLD and r_squared > tc.TRENDING_R_SQUARED_THRESHOLD:
            market_type = 'TRENDING'
        elif efficiency < tc.RANGING_EFFICIENCY_THRESHOLD:
            market_type = 'RANGING'
        else:
            market_type = 'MIXED'
        
        return {
            'type': market_type,
            'efficiency': efficiency,
            'r_squared': r_squared,
            'slope': slope,
            'strength': 'STRONG' if r_squared > 0.7 else 'MEDIUM' if r_squared > 0.4 else 'WEAK'
        }
    
    def _calculate_zone_metadata(self, df: pd.DataFrame, zone_data: Dict, zone_name: str) -> Dict:
        """Calculate additional metadata for zones"""
        if len(df) < tc.ZONE_METADATA_LOOKBACK:
            return {'touches': 0, 'rejections': 0, 'quality': 'LOW'}
        
        # Analyze recent price interaction with zone
        recent_data = df.tail(tc.ZONE_METADATA_LOOKBACK)
        
        touches = 0
        rejections = 0
        
        for _, candle in recent_data.iterrows():
            # Check if candle touched the zone
            if (candle['low'] <= zone_data['upper'] and candle['high'] >= zone_data['lower']):
                touches += 1
                
                # Check for rejection (wick rejection from zone)
                if self._is_zone_rejection(candle, zone_data):
                    rejections += 1
        
        # Assess zone quality
        if rejections >= 2 and touches >= tc.MIN_ZONE_TOUCHES:
            quality = 'HIGH'
        elif rejections >= 1 and touches >= tc.MIN_ZONE_TOUCHES:
            quality = 'MEDIUM'
        else:
            quality = 'LOW'
        
        return {
            'touches': touches,
            'rejections': rejections,
            'quality': quality
        }
    
    def _is_zone_rejection(self, candle: pd.Series, zone_data: Dict) -> bool:
        """Check if candle shows zone rejection"""
        body_top = max(candle['open'], candle['close'])
        body_bottom = min(candle['open'], candle['close'])
        body_size = abs(candle['close'] - candle['open'])
        
        zone_center = zone_data['center']
        
        # Upper wick rejection from resistance
        upper_wick = candle['high'] - body_top
        if (candle['high'] >= zone_center and body_top < zone_center and
            upper_wick > body_size * tc.WICK_REJECTION_RATIO):
            return True
        
        # Lower wick rejection from support
        lower_wick = body_bottom - candle['low']
        if (candle['low'] <= zone_center and body_bottom > zone_center and
            lower_wick > body_size * tc.WICK_REJECTION_RATIO):
            return True
        
        return False

# Configuration class
class DynamicZoneConfig:
    """Configuration for dynamic zone sizing"""
    
    METHODS = {
        'FIXED': 'Fixed-width zones (original)',
        'ATR_BASED': 'Zones based on Average True Range',
        'VOLATILITY_ADAPTIVE': 'Adaptive to volatility changes',
        'TREND_ADAPTIVE': 'Adaptive to trend strength',
        'MARKET_CONDITION': 'Adaptive to market conditions',
        'COMPOSITE_ZONES': 'Combination of multiple factors (recommended)'
    }
    
    @staticmethod
    def get_method_description(method: str) -> str:
        return DynamicZoneConfig.METHODS.get(method, 'Unknown method')