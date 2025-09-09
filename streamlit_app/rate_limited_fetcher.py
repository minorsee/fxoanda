#!/usr/bin/env python3
"""
Rate-Limited Data Fetcher for OANDA API
Handles the 3-pair limit by batching and caching requests
"""

import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class RateLimitedFetcher:
    """
    Smart fetcher that respects OANDA's rate limits
    - Maximum 3 pairs per batch
    - Caches results to avoid repeated API calls
    - Implements backoff strategy for rate limiting
    """
    
    def __init__(self, cache_duration_minutes: int = 10):
        self.oanda = None
        self.cache = {}
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self.last_fetch_time = {}
        self.batch_size = 3  # OANDA limit
        self.batch_delay = 60  # 1 minute between batches
        
        self._initialize_oanda()
    
    def _initialize_oanda(self):
        """Initialize OANDA trader safely"""
        try:
            from oanda_trader import OandaTrader
            self.oanda = OandaTrader()
            print("✅ OANDA API initialized")
        except Exception as e:
            print(f"⚠️ OANDA initialization failed: {e}")
            self.oanda = None
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key].get('timestamp')
        if not cached_time:
            return False
        
        return datetime.now() - cached_time < self.cache_duration
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get data from cache if valid"""
        if self._is_cache_valid(cache_key):
            print(f"📦 Using cached data for {cache_key}")
            return self.cache[cache_key]['data']
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict):
        """Save data to cache"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def _wait_for_rate_limit(self, batch_num: int):
        """Wait between batches to respect rate limits"""
        if batch_num > 0:
            print(f"⏳ Waiting {self.batch_delay}s between batches to respect rate limits...")
            time.sleep(self.batch_delay)
    
    def fetch_single_pair_data(self, instrument: str, months: int = 3) -> Optional[Dict]:
        """
        Fetch data for a single pair with caching
        """
        cache_key = f"{instrument}_{months}m"
        
        # Check cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        if not self.oanda:
            return None
        
        try:
            print(f"📡 Fetching fresh data for {instrument}...")
            
            # Calculate required candles
            days = months * 30
            candle_counts = {
                'D': days + 50,
                'H4': days * 6 + 200,
                'H1': days * 24 + 400
            }
            
            # Fetch multi-timeframe data
            mtf_data = {}
            
            for tf, count in candle_counts.items():
                data = self.oanda.get_candles(instrument, tf, count)
                if data is not None and not data.empty:
                    mtf_data[tf.lower()] = data
                    print(f"  ✓ {tf}: {len(data)} candles")
                else:
                    print(f"  ❌ {tf}: No data")
            
            if mtf_data:
                result = {
                    'instrument': instrument,
                    'mtf_data': mtf_data,
                    'fetch_time': datetime.now()
                }
                
                # Cache the result
                self._save_to_cache(cache_key, result)
                return result
            
            return None
            
        except Exception as e:
            print(f"❌ Error fetching {instrument}: {e}")
            return None
    
    def fetch_multiple_pairs(self, pairs: List[str], months: int = 3) -> Dict[str, Dict]:
        """
        Fetch data for multiple pairs with smart batching
        Automatically splits into batches to respect rate limits
        """
        print(f"🔄 Fetching data for {len(pairs)} pairs (batches of {self.batch_size})")
        
        results = {}
        
        # Process pairs in batches
        for i in range(0, len(pairs), self.batch_size):
            batch_num = i // self.batch_size
            batch_pairs = pairs[i:i + self.batch_size]
            
            print(f"\n📦 Batch {batch_num + 1}: {batch_pairs}")
            
            # Wait between batches (except for first batch)
            self._wait_for_rate_limit(batch_num)
            
            # Process each pair in the current batch
            batch_results = {}
            for pair in batch_pairs:
                result = self.fetch_single_pair_data(pair, months)
                if result:
                    batch_results[pair] = result
                    results[pair] = result
                else:
                    print(f"⚠️ Failed to fetch data for {pair}")
                
                # Small delay between pairs in same batch
                time.sleep(1)
            
            print(f"✅ Batch {batch_num + 1} completed: {len(batch_results)}/{len(batch_pairs)} successful")
        
        print(f"\n🎯 Multi-pair fetch completed: {len(results)}/{len(pairs)} pairs successful")
        return results
    
    def get_cached_pairs(self) -> List[str]:
        """Get list of pairs currently in cache"""
        cached_pairs = []
        for cache_key in self.cache.keys():
            if self._is_cache_valid(cache_key):
                pair = cache_key.split('_')[0]
                cached_pairs.append(pair)
        return list(set(cached_pairs))
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        print("🗑️ Cache cleared")
    
    def get_cache_info(self) -> Dict:
        """Get information about current cache state"""
        valid_entries = sum(1 for key in self.cache.keys() if self._is_cache_valid(key))
        total_entries = len(self.cache)
        
        return {
            'valid_entries': valid_entries,
            'total_entries': total_entries,
            'cached_pairs': self.get_cached_pairs(),
            'cache_duration_minutes': self.cache_duration.total_seconds() / 60
        }

# Convenience functions for easy import
_fetcher_instance = None

def get_fetcher() -> RateLimitedFetcher:
    """Get singleton fetcher instance"""
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = RateLimitedFetcher()
    return _fetcher_instance

def fetch_pairs_safe(pairs: List[str], months: int = 3) -> Dict[str, Dict]:
    """
    Convenience function to fetch multiple pairs safely
    Handles rate limiting automatically
    """
    fetcher = get_fetcher()
    return fetcher.fetch_multiple_pairs(pairs, months)

def fetch_pair_safe(instrument: str, months: int = 3) -> Optional[Dict]:
    """
    Convenience function to fetch single pair safely
    Uses caching to avoid repeated API calls
    """
    fetcher = get_fetcher()
    return fetcher.fetch_single_pair_data(instrument, months)

def get_cache_status() -> Dict:
    """Get current cache status"""
    fetcher = get_fetcher()
    return fetcher.get_cache_info()

def clear_data_cache():
    """Clear all cached data"""
    fetcher = get_fetcher()
    fetcher.clear_cache()

# Test function
def test_rate_limiting():
    """Test the rate limiting functionality"""
    print("🧪 Testing Rate-Limited Fetcher")
    print("="*50)
    
    # Test with a small batch first
    test_pairs = ["EUR_USD", "GBP_USD", "AUD_USD", "NZD_USD", "USD_JPY"]
    
    fetcher = RateLimitedFetcher(cache_duration_minutes=1)  # Short cache for testing
    
    print(f"Testing with {len(test_pairs)} pairs...")
    results = fetcher.fetch_multiple_pairs(test_pairs, months=1)  # Short period for testing
    
    print(f"\n📊 Results Summary:")
    for pair, result in results.items():
        if result:
            mtf_count = len(result.get('mtf_data', {}))
            print(f"  ✅ {pair}: {mtf_count} timeframes")
        else:
            print(f"  ❌ {pair}: Failed")
    
    # Test cache
    print(f"\n📦 Cache Info:")
    cache_info = fetcher.get_cache_info()
    print(f"  Valid entries: {cache_info['valid_entries']}")
    print(f"  Cached pairs: {cache_info['cached_pairs']}")
    
    return len(results) > 0

if __name__ == "__main__":
    success = test_rate_limiting()
    if success:
        print("\n✅ Rate limiting test completed successfully!")
    else:
        print("\n❌ Rate limiting test failed!")