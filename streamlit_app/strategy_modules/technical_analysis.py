import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trading_config as tc

class TechnicalAnalysis:
    """Technical analysis module for EMA/SMA calculations and trend analysis"""
    
    @staticmethod
    def calculate_ema(data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_sma(data: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def calculate_moving_average(data: pd.Series, period: int, use_ema: bool = True) -> pd.Series:
        """Calculate moving average (EMA or SMA based on config)"""
        if use_ema:
            return TechnicalAnalysis.calculate_ema(data, period)
        else:
            return TechnicalAnalysis.calculate_sma(data, period)
    
    @staticmethod
    def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
        """Add all configured moving averages to dataframe"""
        df = df.copy()
        
        # Add fast MA
        df['fast_ma'] = TechnicalAnalysis.calculate_moving_average(
            df['close'], tc.FAST_MA_PERIOD, tc.USE_EMA
        )
        
        # Add slow MA
        df['slow_ma'] = TechnicalAnalysis.calculate_moving_average(
            df['close'], tc.SLOW_MA_PERIOD, tc.USE_EMA
        )
        
        # Add trend MA
        df['trend_ma'] = TechnicalAnalysis.calculate_moving_average(
            df['close'], tc.TREND_MA_PERIOD, tc.USE_EMA
        )
        
        return df
    
    @staticmethod
    def get_trend_bias(df: pd.DataFrame) -> str:
        """
        Determine trend bias based on MA alignment
        Returns: 'BULLISH', 'BEARISH', or 'NEUTRAL'
        """
        if df.empty or len(df) < tc.TREND_MA_PERIOD:
            return 'NEUTRAL'
        
        latest = df.iloc[-1]
        
        # Check MA alignment
        fast_above_slow = latest['fast_ma'] > latest['slow_ma']
        price_above_trend = latest['close'] > latest['trend_ma']
        
        if fast_above_slow and price_above_trend:
            return 'BULLISH'
        elif not fast_above_slow and not price_above_trend:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    @staticmethod
    def create_zones(df: pd.DataFrame, zone_width_pips: float = tc.ZONE_WIDTH_PIPS) -> Dict:
        """
        Create zones around moving averages
        Returns dictionary with zone boundaries
        """
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        
        # Convert pips to price (assuming 4-digit pairs like EUR/USD)
        pip_value = 0.0001
        zone_width = zone_width_pips * pip_value
        
        zones = {
            'fast_ma_zone': {
                'center': latest['fast_ma'],
                'upper': latest['fast_ma'] + zone_width,
                'lower': latest['fast_ma'] - zone_width
            },
            'slow_ma_zone': {
                'center': latest['slow_ma'], 
                'upper': latest['slow_ma'] + zone_width,
                'lower': latest['slow_ma'] - zone_width
            },
            'trend_ma_zone': {
                'center': latest['trend_ma'],
                'upper': latest['trend_ma'] + zone_width,
                'lower': latest['trend_ma'] - zone_width
            }
        }
        
        return zones
    
    @staticmethod
    def is_price_in_zone(price: float, zone: Dict) -> bool:
        """Check if price is within a zone"""
        return zone['lower'] <= price <= zone['upper']
    
    @staticmethod
    def get_zone_interaction(df: pd.DataFrame, lookback: int = 5) -> Dict:
        """
        Analyze recent price interaction with zones
        Returns information about zone touches and rejections
        """
        if len(df) < lookback:
            return {}
        
        recent_df = df.tail(lookback).copy()
        zones = TechnicalAnalysis.create_zones(df)
        
        interactions = {
            'fast_ma_touches': 0,
            'slow_ma_touches': 0, 
            'trend_ma_touches': 0,
            'fast_ma_rejections': 0,
            'slow_ma_rejections': 0,
            'trend_ma_rejections': 0
        }
        
        for _, candle in recent_df.iterrows():
            # Check touches (high/low touched zone)
            for zone_name, zone_data in zones.items():
                zone_key = zone_name.replace('_zone', '')
                
                # Touch detection
                if (candle['low'] <= zone_data['upper'] and 
                    candle['high'] >= zone_data['lower']):
                    interactions[f"{zone_key}_touches"] += 1
                
                # Rejection detection (wick rejection)
                if TechnicalAnalysis._is_wick_rejection(candle, zone_data):
                    interactions[f"{zone_key}_rejections"] += 1
        
        return interactions
    
    @staticmethod
    def _is_wick_rejection(candle: pd.Series, zone: Dict) -> bool:
        """Helper method to detect wick rejections from zones"""
        body_top = max(candle['open'], candle['close'])
        body_bottom = min(candle['open'], candle['close'])
        
        # Upper wick rejection (price rejected from zone resistance)
        if (candle['high'] >= zone['center'] and 
            body_top < zone['center'] and
            (candle['high'] - body_top) > (body_top - body_bottom) * tc.WICK_REJECTION_RATIO):
            return True
        
        # Lower wick rejection (price rejected from zone support)
        if (candle['low'] <= zone['center'] and 
            body_bottom > zone['center'] and
            (body_bottom - candle['low']) > (body_top - body_bottom) * tc.WICK_REJECTION_RATIO):
            return True
        
        return False
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range for volatility measurement"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(window=period).mean()
    
    @staticmethod
    def calculate_volume_profile(df: pd.DataFrame) -> Dict:
        """
        Calculate basic volume analysis
        Returns volume spike information
        """
        if 'volume' not in df.columns or df['volume'].sum() == 0:
            return {'has_volume': False}
        
        df = df.copy()
        df['volume_ma'] = df['volume'].rolling(window=tc.VOLUME_LOOKBACK).mean()
        df['volume_spike'] = df['volume'] > (df['volume_ma'] * tc.VOLUME_SPIKE_MULTIPLIER)
        
        latest = df.iloc[-1]
        recent_spikes = df['volume_spike'].tail(5).sum()
        
        return {
            'has_volume': True,
            'current_volume': latest['volume'],
            'average_volume': latest['volume_ma'],
            'is_spike': latest['volume_spike'],
            'recent_spikes': recent_spikes,
            'volume_ratio': latest['volume'] / latest['volume_ma'] if latest['volume_ma'] > 0 else 0
        }