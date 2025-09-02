# Trading Configuration - Adjust parameters here
# Zone-based trading system parameters

# === TIMEFRAMES ===
TREND_TIMEFRAME = "D"      # Daily for trend bias
ZONE_TIMEFRAME = "H4"      # H4 for zones
EXECUTION_TIMEFRAME = "H1" # H1 for entries

# === EMA/SMA PERIODS ===
FAST_MA_PERIOD = 21
SLOW_MA_PERIOD = 50
TREND_MA_PERIOD = 200

# Use EMA (True) or SMA (False)
USE_EMA = True

# === ZONE PARAMETERS ===
# Zone width around MA (in pips)
ZONE_WIDTH_PIPS = 15

# Minimum zone touch confirmation
MIN_ZONE_TOUCHES = 2

# === PRICE ACTION PARAMETERS ===
# Wick rejection ratio (wick must be X times larger than body)
WICK_REJECTION_RATIO = 2.0

# Engulfing candle minimum body size (in pips)
MIN_ENGULFING_BODY_PIPS = 5

# === VOLUME PARAMETERS ===
# Volume spike multiplier (current volume > avg volume * multiplier)
VOLUME_SPIKE_MULTIPLIER = 1.5

# Volume lookback periods for average calculation
VOLUME_LOOKBACK = 20

# === ENTRY PARAMETERS ===
# Risk per trade (percentage of account)
RISK_PERCENT = 1.0

# Risk-reward ratio (sweet spot for quality vs frequency)
RISK_REWARD_RATIO = 1.7

# Maximum spread allowed (in pips)
MAX_SPREAD_PIPS = 3

# === INSTRUMENTS ===
DEFAULT_INSTRUMENT = "EUR_USD"

# ============================================================================
# MODULAR STRATEGY ENHANCEMENTS - PLUG AND PLAY CONFIGURATION
# ============================================================================

# === ENTRY TIMING METHODS ===
# Choose your entry timing method:
# - IMMEDIATE: Enter immediately when price is in zone (original)
# - ZONE_REJECTION: Wait for zone rejection confirmation (recommended)
# - PULLBACK_COMPLETION: Enter after pullback completion
# - BREAKOUT_RETEST: Enter on breakout retest
# - CONFLUENCE_CONFIRMATION: Multiple confirmation required
ENTRY_TIMING_METHOD = "ZONE_REJECTION"

# Entry timing parameters
PULLBACK_LOOKBACK = 10
BREAKOUT_LOOKBACK = 20
MIN_CONFLUENCE_CONFIRMATIONS = 2
VOLUME_CONFIRMATION_MULTIPLIER = 1.3

# === ENHANCED TREND ANALYSIS METHODS ===
# Choose your trend analysis method:
# - MA_ALIGNMENT: Traditional MA alignment (enhanced)
# - SLOPE_ANALYSIS: Trend based on MA slopes and momentum
# - MARKET_STRUCTURE: Swing high/low analysis
# - MOMENTUM_TREND: RSI, ROC, and momentum indicators
# - MULTI_TIMEFRAME: Multi-timeframe trend analysis
# - COMPOSITE_TREND: Combination of multiple methods (recommended)
TREND_ANALYSIS_METHOD = "COMPOSITE_TREND"

# Slope analysis parameters
SLOPE_LOOKBACK = 20
SLOPE_FAST_PERIOD = 5
SLOPE_SLOW_PERIOD = 10
SLOPE_TREND_PERIOD = 15
SLOPE_PRICE_PERIOD = 8
SLOPE_THRESHOLD = 0.01

# Market structure parameters
STRUCTURE_LOOKBACK = 50
SWING_DETECTION_PERIOD = 5
MAX_SWING_POINTS = 10

# Momentum parameters
MOMENTUM_LOOKBACK = 30
ROC_PERIOD = 10
RSI_PERIOD = 14
MOMENTUM_PERIOD = 12
ROC_BULLISH_THRESHOLD = 2.0
ROC_BEARISH_THRESHOLD = -2.0
MOMENTUM_THRESHOLD = 0.5

# Multi-timeframe parameters
TIMEFRAME_WEIGHTS = {
    'daily': 3.0,    # Highest weight for daily trend
    'h4': 2.0,       # Medium weight for H4
    'h1': 1.0        # Lowest weight for H1
}
MTF_BULLISH_THRESHOLD = 0.3
MTF_BEARISH_THRESHOLD = -0.3
MTF_STRONG_THRESHOLD = 0.6

# === DYNAMIC ZONE SIZING METHODS ===
# Choose your zone sizing method:
# - FIXED: Fixed-width zones (original)
# - ATR_BASED: Zones based on Average True Range
# - VOLATILITY_ADAPTIVE: Adaptive to volatility changes
# - TREND_ADAPTIVE: Adaptive to trend strength
# - MARKET_CONDITION: Adaptive to market conditions
# - COMPOSITE_ZONES: Combination of multiple factors (recommended)
ZONE_SIZING_METHOD = "COMPOSITE_ZONES"

# ATR-based zone parameters
ATR_PERIOD = 14
ATR_ZONE_MULTIPLIER = 0.75

# Volatility adaptive parameters
VOLATILITY_LOOKBACK = 30
HIGH_VOLATILITY_MULTIPLIER = 1.2
LOW_VOLATILITY_MULTIPLIER = 0.6
NORMAL_VOLATILITY_MULTIPLIER = 0.8

# Trend adaptive parameters
STRONG_TREND_ZONE_MULTIPLIER = 0.7    # Tighter zones in strong trends
MEDIUM_TREND_ZONE_MULTIPLIER = 0.9
WEAK_TREND_ZONE_MULTIPLIER = 1.2     # Wider zones in weak trends

# Market condition parameters
MARKET_CONDITION_LOOKBACK = 40
TRENDING_MARKET_MULTIPLIER = 0.8      # Tighter zones in trending markets
RANGING_MARKET_MULTIPLIER = 1.3       # Wider zones in ranging markets
MIXED_MARKET_MULTIPLIER = 1.0
TRENDING_EFFICIENCY_THRESHOLD = 0.6
RANGING_EFFICIENCY_THRESHOLD = 0.3
TRENDING_R_SQUARED_THRESHOLD = 0.5

# Composite zone weights
COMPOSITE_ZONE_WEIGHTS = {
    'atr': 0.4,
    'volatility': 0.3,
    'market_condition': 0.3
}

# Zone metadata parameters
ZONE_METADATA_LOOKBACK = 20

# === PRICE ACTION CONFIRMATION METHODS ===
# Choose your price action method:
# - BASIC_PATTERNS: Basic candlestick patterns
# - REVERSAL_PATTERNS: Focus on reversal patterns
# - CONTINUATION_PATTERNS: Focus on continuation patterns
# - MOMENTUM_PATTERNS: Focus on momentum patterns
# - CONFLUENCE_PATTERNS: Multiple pattern confluence
# - COMPREHENSIVE: All pattern types (recommended)
PRICE_ACTION_METHOD = "COMPREHENSIVE"

# General pattern parameters
MIN_CANDLES_FOR_PATTERNS = 5

# Candlestick pattern parameters
DOJI_BODY_RATIO = 0.1
HAMMER_WICK_RATIO = 2.0
HAMMER_UPPER_WICK_RATIO = 0.5
SHOOTING_STAR_WICK_RATIO = 2.0
SHOOTING_STAR_LOWER_WICK_RATIO = 0.5
MARUBOZU_BODY_RATIO = 0.9
ENGULFING_SIZE_RATIO = 1.2

# Pin bar parameters
PIN_BAR_WICK_RATIO = 0.6
PIN_BAR_OPPOSITE_WICK_RATIO = 0.2
PIN_BAR_BODY_RATIO = 0.3

# Star pattern parameters
STAR_BODY_RATIO = 0.3

# Pattern lookback periods
REVERSAL_PATTERN_LOOKBACK = 5
CONTINUATION_PATTERN_LOOKBACK = 10
MOMENTUM_PATTERN_LOOKBACK = 8

# Continuation pattern parameters
FLAG_PATTERN_MIN_CANDLES = 5
FLAG_CONSOLIDATION_RATIO = 0.4
FLAG_TREND_THRESHOLD = 0.02

# Breakout parameters
BREAKOUT_LOOKBACK = 10
BREAKOUT_THRESHOLD = 0.005

# Momentum pattern parameters
STRONG_CLOSE_THRESHOLD = 0.8
MIN_GAP_SIZE = 0.002
VOLUME_PATTERN_LOOKBACK = 10
HIGH_VOLUME_MULTIPLIER = 2.0
DIVERGENCE_LOOKBACK = 15
MOMENTUM_DIVERGENCE_THRESHOLD = 0.01

# Pattern enhancement parameters
ZONE_CONTEXT_BONUS = 15
TREND_ALIGNMENT_BONUS = 10
ZONE_PROXIMITY_RATIO = 0.5
MIN_CONFLUENCE_PATTERNS = 2
MULTIPLE_CONFLUENCE_BONUS = 5

# ============================================================================
# EASY PLUG-AND-PLAY PRESETS
# ============================================================================

def use_conservative_settings():
    """Apply conservative settings - fewer but higher quality trades"""
    global ENTRY_TIMING_METHOD, TREND_ANALYSIS_METHOD, ZONE_SIZING_METHOD, PRICE_ACTION_METHOD
    global MIN_CONFLUENCE_CONFIRMATIONS, ATR_ZONE_MULTIPLIER
    
    ENTRY_TIMING_METHOD = "CONFLUENCE_CONFIRMATION"
    TREND_ANALYSIS_METHOD = "COMPOSITE_TREND"
    ZONE_SIZING_METHOD = "COMPOSITE_ZONES"
    PRICE_ACTION_METHOD = "COMPREHENSIVE"
    MIN_CONFLUENCE_CONFIRMATIONS = 3
    ATR_ZONE_MULTIPLIER = 1.0
    print("✅ Applied CONSERVATIVE settings")

def use_aggressive_settings():
    """Apply aggressive settings - more trades, potentially lower quality"""
    global ENTRY_TIMING_METHOD, TREND_ANALYSIS_METHOD, ZONE_SIZING_METHOD, PRICE_ACTION_METHOD
    global MIN_CONFLUENCE_CONFIRMATIONS, ATR_ZONE_MULTIPLIER
    
    ENTRY_TIMING_METHOD = "ZONE_REJECTION"
    TREND_ANALYSIS_METHOD = "MA_ALIGNMENT"
    ZONE_SIZING_METHOD = "ATR_BASED"
    PRICE_ACTION_METHOD = "BASIC_PATTERNS"
    MIN_CONFLUENCE_CONFIRMATIONS = 1
    ATR_ZONE_MULTIPLIER = 0.5
    print("✅ Applied AGGRESSIVE settings")

def use_balanced_settings():
    """Apply balanced settings - good mix of frequency and quality"""
    global ENTRY_TIMING_METHOD, TREND_ANALYSIS_METHOD, ZONE_SIZING_METHOD, PRICE_ACTION_METHOD
    global MIN_CONFLUENCE_CONFIRMATIONS, ATR_ZONE_MULTIPLIER
    
    ENTRY_TIMING_METHOD = "ZONE_REJECTION"
    TREND_ANALYSIS_METHOD = "COMPOSITE_TREND"
    ZONE_SIZING_METHOD = "VOLATILITY_ADAPTIVE"
    PRICE_ACTION_METHOD = "REVERSAL_PATTERNS"
    MIN_CONFLUENCE_CONFIRMATIONS = 2
    ATR_ZONE_MULTIPLIER = 0.75
    print("✅ Applied BALANCED settings")

def use_original_settings():
    """Revert to original strategy settings"""
    global ENTRY_TIMING_METHOD, TREND_ANALYSIS_METHOD, ZONE_SIZING_METHOD, PRICE_ACTION_METHOD
    
    ENTRY_TIMING_METHOD = "IMMEDIATE"
    TREND_ANALYSIS_METHOD = "MA_ALIGNMENT"
    ZONE_SIZING_METHOD = "FIXED"
    PRICE_ACTION_METHOD = "BASIC_PATTERNS"
    print("✅ Applied ORIGINAL settings")

# Default to balanced settings
use_aggressive_settings()  # Uncomment to apply automatically

# Major pairs to analyze
MAJOR_PAIRS = [
    "EUR_USD", "GBP_USD", 
    "USD_JPY", "USD_CHF", "AUD_USD", 
    "USD_CAD", "NZD_USD"
]

# === DATA PARAMETERS ===
# Number of candles to fetch for analysis
CANDLE_COUNT = {
    "D": 100,   # Daily
    "H4": 200,  # 4-hour  
    "H1": 500   # 1-hour
}

# === DISPLAY PARAMETERS ===
# Show debug information
DEBUG_MODE = True

# Chart display settings
CHART_WIDTH = 15
CHART_HEIGHT = 10

# Colors for zones
BULLISH_ZONE_COLOR = '#26a69a'
BEARISH_ZONE_COLOR = '#ef5350'
NEUTRAL_ZONE_COLOR = '#ffa726'