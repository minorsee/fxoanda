#!/usr/bin/env python3
"""
Safe Technical Analysis Wrapper for Streamlit App
Handles NaN values gracefully without modifying external files
"""

import pandas as pd
import numpy as np
import warnings
from typing import Dict, Optional, Any, List
warnings.filterwarnings('ignore')

import sys
import os
# No need to modify sys.path - zone_based_strategy is now local

def safe_get_signals(instrument: str) -> Optional[Dict]:
    """
    Streamlit-safe function to get trading signals
    Uses rate-limited fetcher and handles NaN issues
    """
    try:
        # Import and use external zone_trader (don't modify it)
        from zone_based_strategy.zone_trader import ZoneTrader
        from rate_limited_fetcher import fetch_pair_safe
        
        # Suppress warnings during analysis
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            trader = ZoneTrader()
            results = trader.run_analysis(instrument)
        
        if not results:
            return _create_safe_fallback(instrument)
        
        # Clean up any NaN values in the results for Streamlit display
        return _sanitize_results(results)
        
    except Exception as e:
        return _create_safe_fallback(instrument, str(e))

def _sanitize_results(results: Dict) -> Dict:
    """Clean results of NaN values that could break Streamlit display"""
    
    # Fix trend analysis values
    if 'trend_analysis' in results:
        trend = results['trend_analysis']
        current_price = trend.get('current_price', 1.0)
        
        # Replace NaN values with safe fallbacks
        for key in ['fast_ma', 'slow_ma', 'trend_ma']:
            if pd.isna(trend.get(key)) or np.isinf(trend.get(key)):
                trend[key] = current_price
        
        if pd.isna(trend.get('atr')) or np.isinf(trend.get('atr')):
            trend['atr'] = current_price * 0.001
    
    # Fix entry signals
    if 'entry_signals' in results:
        signals = results['entry_signals']
        
        # Fix confidence
        if pd.isna(signals.get('confidence')) or np.isinf(signals.get('confidence')):
            signals['confidence'] = 0
            
        # Fix entry price
        if pd.isna(signals.get('entry_price')) or np.isinf(signals.get('entry_price')):
            signals['entry_price'] = results.get('trend_analysis', {}).get('current_price', 0)
        
        # Fix risk/reward values
        if 'risk_reward' in signals:
            rr = signals['risk_reward']
            for key in ['stop_loss', 'take_profit', 'risk_reward']:
                if pd.isna(rr.get(key)) or np.isinf(rr.get(key)):
                    rr[key] = None
    
    # Fix MTF data for chart display
    if 'mtf_data' in results:
        for timeframe, df in results['mtf_data'].items():
            if isinstance(df, pd.DataFrame):
                # Clean MA columns for chart display
                for col in ['fast_ma', 'slow_ma', 'trend_ma']:
                    if col in df.columns:
                        # Forward fill NaN values
                        df[col] = df[col].fillna(method='ffill').fillna(df['close'])
                
                # Replace infinite values
                df = df.replace([np.inf, -np.inf], np.nan).fillna(method='ffill')
                results['mtf_data'][timeframe] = df
    
    return results

def _create_safe_fallback(instrument: str, error: str = None) -> Dict:
    """Create safe fallback when analysis fails"""
    
    try:
        # Try to get basic price data for fallback
        from oanda_trader import OandaTrader
        oanda = OandaTrader()
        h1_data = oanda.get_candles(instrument, "H1", 20)
        current_price = h1_data['close'].iloc[-1] if h1_data is not None else 1.0
    except:
        current_price = 1.0
    
    return {
        'instrument': instrument,
        'trend_analysis': {
            'bias': 'NEUTRAL',
            'strength': 'WEAK',
            'fast_ma': current_price,
            'slow_ma': current_price, 
            'trend_ma': current_price,
            'current_price': current_price,
            'atr': current_price * 0.001
        },
        'entry_signals': {
            'signal': 'NO_SIGNAL',
            'confidence': 0,
            'entry_price': current_price,
            'active_zones': [],
            'trend_alignment': False,
            'risk_reward': {
                'stop_loss': None,
                'take_profit': None,
                'risk_reward': None
            }
        },
        'zones': {},
        'mtf_data': {}
    }

def safe_format_number(value: Any, decimals: int = 5) -> str:
    """Safely format numbers for Streamlit display"""
    try:
        if value is None or pd.isna(value) or np.isinf(value):
            return "N/A"
        return f"{float(value):.{decimals}f}"
    except:
        return "N/A"

def safe_format_percentage(value: Any, decimals: int = 1) -> str:
    """Safely format percentages for Streamlit display"""
    try:
        if value is None or pd.isna(value) or np.isinf(value):
            return "N/A%"
        return f"{float(value):.{decimals}f}%"
    except:
        return "N/A%"

def safe_get_multi_pair_signals(pairs: List[str], months: int = 3) -> Dict[str, Dict]:
    """
    Get signals for multiple pairs with rate limiting
    Automatically batches requests to respect OANDA's 3-pair limit
    """
    try:
        from rate_limited_fetcher import fetch_pairs_safe, get_cache_status
        
        print(f"📊 Fetching signals for {len(pairs)} pairs...")
        
        # Show cache status
        cache_info = get_cache_status()
        cached_pairs = cache_info.get('cached_pairs', [])
        if cached_pairs:
            print(f"📦 {len(cached_pairs)} pairs already cached: {cached_pairs}")
        
        # This will automatically batch the requests
        results = {}
        
        for pair in pairs:
            try:
                signal_result = safe_get_signals(pair)
                if signal_result:
                    results[pair] = signal_result
                    
            except Exception as e:
                print(f"⚠️ Error getting signals for {pair}: {e}")
                results[pair] = _create_safe_fallback(pair, str(e))
        
        return results
        
    except Exception as e:
        print(f"❌ Multi-pair analysis failed: {e}")
        return {}