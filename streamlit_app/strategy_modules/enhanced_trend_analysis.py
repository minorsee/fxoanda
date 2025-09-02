"""
Enhanced Trend Analysis Module
Advanced trend detection with momentum, market structure, and multi-timeframe analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trading_config as tc

class EnhancedTrendAnalysis:
    """
    Advanced trend analysis system with multiple trend detection methods
    """
    
    def __init__(self):
        self.trend_methods = {
            'MA_ALIGNMENT': self._ma_alignment_trend,
            'SLOPE_ANALYSIS': self._slope_analysis_trend,
            'MARKET_STRUCTURE': self._market_structure_trend,
            'MOMENTUM_TREND': self._momentum_trend,
            'MULTI_TIMEFRAME': self._multi_timeframe_trend,
            'COMPOSITE_TREND': self._composite_trend
        }
    
    def get_trend_analysis(self, df: pd.DataFrame, 
                          method: str = tc.TREND_ANALYSIS_METHOD,
                          mtf_data: Dict = None) -> Dict:
        """
        Main entry point for trend analysis
        
        Args:
            df: Primary timeframe dataframe
            method: Trend analysis method to use
            mtf_data: Multi-timeframe data dictionary
            
        Returns:
            Dict with comprehensive trend analysis
        """
        if method not in self.trend_methods:
            raise ValueError(f"Unknown trend method: {method}")
        
        # Get base trend analysis
        trend_result = self.trend_methods[method](df, mtf_data)
        
        # Add common trend metrics
        trend_result.update(self._calculate_trend_metrics(df))
        
        return trend_result
    
    def _ma_alignment_trend(self, df: pd.DataFrame, mtf_data: Dict = None) -> Dict:
        """
        Original MA alignment method (enhanced)
        """
        if df.empty or len(df) < tc.TREND_MA_PERIOD:
            return self._neutral_trend()
        
        latest = df.iloc[-1]
        
        # Basic MA alignment
        fast_above_slow = latest['fast_ma'] > latest['slow_ma']
        price_above_trend = latest['close'] > latest['trend_ma']
        slow_above_trend = latest['slow_ma'] > latest['trend_ma']
        
        # Enhanced alignment score
        alignment_score = 0
        if fast_above_slow: alignment_score += 1
        if price_above_trend: alignment_score += 1
        if slow_above_trend: alignment_score += 1
        
        if alignment_score >= 2:
            bias = 'BULLISH'
            strength = 'STRONG' if alignment_score == 3 else 'MEDIUM'
        elif alignment_score <= 1:
            # Check for bearish alignment
            bear_score = 0
            if not fast_above_slow: bear_score += 1
            if not price_above_trend: bear_score += 1
            if not slow_above_trend: bear_score += 1
            
            if bear_score >= 2:
                bias = 'BEARISH'
                strength = 'STRONG' if bear_score == 3 else 'MEDIUM'
            else:
                bias = 'NEUTRAL'
                strength = 'WEAK'
        else:
            bias = 'NEUTRAL'
            strength = 'WEAK'
        
        return {
            'method': 'MA_ALIGNMENT',
            'bias': bias,
            'strength': strength,
            'confidence': self._calculate_ma_confidence(alignment_score, 3),
            'alignment_score': alignment_score
        }
    
    def _slope_analysis_trend(self, df: pd.DataFrame, mtf_data: Dict = None) -> Dict:
        """
        Trend analysis based on MA slopes and momentum
        """
        if len(df) < tc.SLOPE_LOOKBACK:
            return self._neutral_trend()
        
        # Calculate slopes for different periods
        fast_ma_slope = self._calculate_slope(df['fast_ma'], tc.SLOPE_FAST_PERIOD)
        slow_ma_slope = self._calculate_slope(df['slow_ma'], tc.SLOPE_SLOW_PERIOD)
        trend_ma_slope = self._calculate_slope(df['trend_ma'], tc.SLOPE_TREND_PERIOD)
        price_slope = self._calculate_slope(df['close'], tc.SLOPE_PRICE_PERIOD)
        
        # Normalize slopes relative to ATR
        atr = df['high'].subtract(df['low']).rolling(14).mean().iloc[-1]
        
        slopes = {
            'fast_ma': fast_ma_slope / atr,
            'slow_ma': slow_ma_slope / atr,
            'trend_ma': trend_ma_slope / atr,
            'price': price_slope / atr
        }
        
        # Determine trend based on slope analysis
        bullish_slopes = sum(1 for slope in slopes.values() if slope > tc.SLOPE_THRESHOLD)
        bearish_slopes = sum(1 for slope in slopes.values() if slope < -tc.SLOPE_THRESHOLD)
        
        if bullish_slopes >= 3:
            bias = 'BULLISH'
            strength = 'STRONG' if bullish_slopes == 4 else 'MEDIUM'
        elif bearish_slopes >= 3:
            bias = 'BEARISH'
            strength = 'STRONG' if bearish_slopes == 4 else 'MEDIUM'
        else:
            bias = 'NEUTRAL'
            strength = 'WEAK'
        
        return {
            'method': 'SLOPE_ANALYSIS',
            'bias': bias,
            'strength': strength,
            'confidence': self._calculate_slope_confidence(bullish_slopes, bearish_slopes),
            'slopes': slopes,
            'bullish_slopes': bullish_slopes,
            'bearish_slopes': bearish_slopes
        }
    
    def _market_structure_trend(self, df: pd.DataFrame, mtf_data: Dict = None) -> Dict:
        """
        Trend analysis based on market structure (swing highs/lows)
        """
        if len(df) < tc.STRUCTURE_LOOKBACK:
            return self._neutral_trend()
        
        # Identify swing points
        swing_highs = self._identify_swing_points(df['high'], tc.SWING_DETECTION_PERIOD, 'high')
        swing_lows = self._identify_swing_points(df['low'], tc.SWING_DETECTION_PERIOD, 'low')
        
        # Analyze structure
        structure_analysis = self._analyze_market_structure(swing_highs, swing_lows)
        
        return {
            'method': 'MARKET_STRUCTURE',
            'bias': structure_analysis['bias'],
            'strength': structure_analysis['strength'],
            'confidence': structure_analysis['confidence'],
            'swing_highs': swing_highs,
            'swing_lows': swing_lows,
            'structure_details': structure_analysis
        }
    
    def _momentum_trend(self, df: pd.DataFrame, mtf_data: Dict = None) -> Dict:
        """
        Trend analysis based on momentum indicators
        """
        if len(df) < tc.MOMENTUM_LOOKBACK:
            return self._neutral_trend()
        
        # Calculate momentum indicators
        roc = self._calculate_rate_of_change(df['close'], tc.ROC_PERIOD)
        rsi = self._calculate_rsi(df['close'], tc.RSI_PERIOD)
        momentum = self._calculate_momentum(df['close'], tc.MOMENTUM_PERIOD)
        
        # Momentum-based trend determination
        momentum_score = 0
        
        # ROC analysis
        if roc.iloc[-1] > tc.ROC_BULLISH_THRESHOLD:
            momentum_score += 2
        elif roc.iloc[-1] > 0:
            momentum_score += 1
        elif roc.iloc[-1] < tc.ROC_BEARISH_THRESHOLD:
            momentum_score -= 2
        elif roc.iloc[-1] < 0:
            momentum_score -= 1
        
        # RSI analysis
        latest_rsi = rsi.iloc[-1]
        if latest_rsi > 60:
            momentum_score += 1
        elif latest_rsi < 40:
            momentum_score -= 1
        
        # Momentum analysis
        if momentum.iloc[-1] > tc.MOMENTUM_THRESHOLD:
            momentum_score += 1
        elif momentum.iloc[-1] < -tc.MOMENTUM_THRESHOLD:
            momentum_score -= 1
        
        # Determine trend
        if momentum_score >= 3:
            bias = 'BULLISH'
            strength = 'STRONG'
        elif momentum_score >= 1:
            bias = 'BULLISH'
            strength = 'MEDIUM' if momentum_score >= 2 else 'WEAK'
        elif momentum_score <= -3:
            bias = 'BEARISH'
            strength = 'STRONG'
        elif momentum_score <= -1:
            bias = 'BEARISH'
            strength = 'MEDIUM' if momentum_score <= -2 else 'WEAK'
        else:
            bias = 'NEUTRAL'
            strength = 'WEAK'
        
        return {
            'method': 'MOMENTUM_TREND',
            'bias': bias,
            'strength': strength,
            'confidence': min(abs(momentum_score) * 15 + 40, 90),
            'momentum_score': momentum_score,
            'roc': roc.iloc[-1],
            'rsi': latest_rsi,
            'momentum': momentum.iloc[-1]
        }
    
    def _multi_timeframe_trend(self, df: pd.DataFrame, mtf_data: Dict = None) -> Dict:
        """
        Multi-timeframe trend analysis
        """
        if not mtf_data:
            return self._ma_alignment_trend(df)
        
        # Analyze each timeframe
        timeframe_trends = {}
        
        for tf, tf_data in mtf_data.items():
            if tf_data is not None and not tf_data.empty:
                tf_trend = self._ma_alignment_trend(tf_data)
                timeframe_trends[tf] = tf_trend
        
        # Weight timeframes by importance
        weights = tc.TIMEFRAME_WEIGHTS
        weighted_score = 0
        total_weight = 0
        
        for tf, trend_data in timeframe_trends.items():
            weight = weights.get(tf, 1.0)
            if trend_data['bias'] == 'BULLISH':
                weighted_score += weight * trend_data['confidence'] / 100
            elif trend_data['bias'] == 'BEARISH':
                weighted_score -= weight * trend_data['confidence'] / 100
            total_weight += weight
        
        if total_weight > 0:
            weighted_score /= total_weight
        
        # Determine overall trend
        if weighted_score > tc.MTF_BULLISH_THRESHOLD:
            bias = 'BULLISH'
            strength = 'STRONG' if weighted_score > tc.MTF_STRONG_THRESHOLD else 'MEDIUM'
        elif weighted_score < tc.MTF_BEARISH_THRESHOLD:
            bias = 'BEARISH'
            strength = 'STRONG' if weighted_score < -tc.MTF_STRONG_THRESHOLD else 'MEDIUM'
        else:
            bias = 'NEUTRAL'
            strength = 'WEAK'
        
        return {
            'method': 'MULTI_TIMEFRAME',
            'bias': bias,
            'strength': strength,
            'confidence': min(abs(weighted_score) * 100 + 40, 95),
            'weighted_score': weighted_score,
            'timeframe_trends': timeframe_trends
        }
    
    def _composite_trend(self, df: pd.DataFrame, mtf_data: Dict = None) -> Dict:
        """
        Composite trend analysis using multiple methods
        """
        methods = ['MA_ALIGNMENT', 'SLOPE_ANALYSIS', 'MOMENTUM_TREND']
        if mtf_data:
            methods.append('MULTI_TIMEFRAME')
        
        trend_results = []
        for method in methods:
            try:
                result = self.trend_methods[method](df, mtf_data)
                trend_results.append(result)
            except Exception as e:
                print(f"Error in {method}: {e}")
        
        if not trend_results:
            return self._neutral_trend()
        
        # Combine results
        bullish_votes = sum(1 for r in trend_results if r['bias'] == 'BULLISH')
        bearish_votes = sum(1 for r in trend_results if r['bias'] == 'BEARISH')
        
        # Weight by confidence
        weighted_bullish = sum(r['confidence'] for r in trend_results if r['bias'] == 'BULLISH')
        weighted_bearish = sum(r['confidence'] for r in trend_results if r['bias'] == 'BEARISH')
        
        total_confidence = sum(r['confidence'] for r in trend_results)
        
        if bullish_votes > bearish_votes or weighted_bullish > weighted_bearish:
            bias = 'BULLISH'
            strength = 'STRONG' if bullish_votes >= 3 else 'MEDIUM'
            confidence = weighted_bullish / len([r for r in trend_results if r['bias'] == 'BULLISH']) if bullish_votes > 0 else 50
        elif bearish_votes > bullish_votes or weighted_bearish > weighted_bullish:
            bias = 'BEARISH'
            strength = 'STRONG' if bearish_votes >= 3 else 'MEDIUM'
            confidence = weighted_bearish / len([r for r in trend_results if r['bias'] == 'BEARISH']) if bearish_votes > 0 else 50
        else:
            bias = 'NEUTRAL'
            strength = 'WEAK'
            confidence = 40
        
        return {
            'method': 'COMPOSITE_TREND',
            'bias': bias,
            'strength': strength,
            'confidence': min(int(confidence), 95),
            'component_results': trend_results,
            'bullish_votes': bullish_votes,
            'bearish_votes': bearish_votes
        }
    
    # Helper methods
    def _calculate_slope(self, series: pd.Series, period: int) -> float:
        """Calculate slope of a series over given period"""
        if len(series) < period:
            return 0.0
        
        y = series.tail(period).values
        x = np.arange(len(y))
        
        if len(x) < 2:
            return 0.0
        
        return np.polyfit(x, y, 1)[0]
    
    def _calculate_trend_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate common trend metrics"""
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        
        # MA separation (trend strength indicator)
        fast_slow_sep = abs(latest['fast_ma'] - latest['slow_ma'])
        price_trend_sep = abs(latest['close'] - latest['trend_ma'])
        
        # ATR for normalization
        atr = df['high'].subtract(df['low']).rolling(14).mean().iloc[-1]
        
        return {
            'ma_separation': fast_slow_sep / atr if atr > 0 else 0,
            'price_trend_separation': price_trend_sep / atr if atr > 0 else 0,
            'current_price': latest['close'],
            'fast_ma': latest['fast_ma'],
            'slow_ma': latest['slow_ma'],
            'trend_ma': latest['trend_ma'],
            'atr': atr
        }
    
    def _neutral_trend(self) -> Dict:
        """Return neutral trend result"""
        return {
            'bias': 'NEUTRAL',
            'strength': 'WEAK',
            'confidence': 30
        }
    
    def _calculate_ma_confidence(self, score: int, max_score: int) -> int:
        """Calculate confidence based on MA alignment score"""
        return min(40 + (score / max_score) * 40, 85)
    
    def _calculate_slope_confidence(self, bullish_slopes: int, bearish_slopes: int) -> int:
        """Calculate confidence based on slope analysis"""
        dominant_slopes = max(bullish_slopes, bearish_slopes)
        return min(40 + dominant_slopes * 15, 90)
    
    def _identify_swing_points(self, series: pd.Series, period: int, point_type: str) -> List[Tuple]:
        """Identify swing highs or lows"""
        # Simplified swing point detection
        swings = []
        if len(series) < period * 2 + 1:
            return swings
        
        for i in range(period, len(series) - period):
            window = series.iloc[i-period:i+period+1]
            
            if point_type == 'high' and series.iloc[i] == window.max():
                swings.append((i, series.iloc[i]))
            elif point_type == 'low' and series.iloc[i] == window.min():
                swings.append((i, series.iloc[i]))
        
        return swings[-tc.MAX_SWING_POINTS:]  # Keep only recent swings
    
    def _analyze_market_structure(self, swing_highs: List[Tuple], swing_lows: List[Tuple]) -> Dict:
        """Analyze market structure for trend direction"""
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {'bias': 'NEUTRAL', 'strength': 'WEAK', 'confidence': 30}
        
        # Higher highs and higher lows = bullish
        # Lower highs and lower lows = bearish
        
        recent_highs = [price for _, price in swing_highs[-2:]]
        recent_lows = [price for _, price in swing_lows[-2:]]
        
        higher_highs = recent_highs[-1] > recent_highs[0]
        higher_lows = recent_lows[-1] > recent_lows[0]
        lower_highs = recent_highs[-1] < recent_highs[0]
        lower_lows = recent_lows[-1] < recent_lows[0]
        
        if higher_highs and higher_lows:
            return {'bias': 'BULLISH', 'strength': 'STRONG', 'confidence': 80}
        elif higher_highs or higher_lows:
            return {'bias': 'BULLISH', 'strength': 'MEDIUM', 'confidence': 65}
        elif lower_highs and lower_lows:
            return {'bias': 'BEARISH', 'strength': 'STRONG', 'confidence': 80}
        elif lower_highs or lower_lows:
            return {'bias': 'BEARISH', 'strength': 'MEDIUM', 'confidence': 65}
        else:
            return {'bias': 'NEUTRAL', 'strength': 'WEAK', 'confidence': 40}
    
    def _calculate_rate_of_change(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Rate of Change"""
        return ((series - series.shift(period)) / series.shift(period)) * 100
    
    def _calculate_rsi(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate RSI"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_momentum(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Momentum"""
        return series - series.shift(period)

# Configuration class
class EnhancedTrendConfig:
    """Configuration for enhanced trend analysis"""
    
    METHODS = {
        'MA_ALIGNMENT': 'Traditional MA alignment (enhanced)',
        'SLOPE_ANALYSIS': 'Trend based on MA slopes and momentum',
        'MARKET_STRUCTURE': 'Swing high/low analysis',
        'MOMENTUM_TREND': 'RSI, ROC, and momentum indicators',
        'MULTI_TIMEFRAME': 'Multi-timeframe trend analysis',
        'COMPOSITE_TREND': 'Combination of multiple methods (recommended)'
    }
    
    @staticmethod
    def get_method_description(method: str) -> str:
        return EnhancedTrendConfig.METHODS.get(method, 'Unknown method')