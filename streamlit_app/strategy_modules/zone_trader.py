import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from oanda_trader import OandaTrader
from strategy_modules.technical_analysis import TechnicalAnalysis
from strategy_modules.price_action import PriceAction
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import trading_config as tc

class ZoneTrader:
    """
    Multi-timeframe zone-based trading system
    Think in zones, not lines - Use EMAs/SMAs as maps
    """
    
    def __init__(self):
        self.oanda = OandaTrader()
        self.ta = TechnicalAnalysis()
        self.pa = PriceAction()
    
    def get_multi_timeframe_data(self, instrument: str = tc.DEFAULT_INSTRUMENT) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for all required timeframes
        Returns dictionary with DataFrames for each timeframe
        """
        if tc.DEBUG_MODE:
            print(f"Fetching multi-timeframe data for {instrument}...")
        
        mtf_data = {}
        
        try:
            # Daily data for trend bias
            daily_data = self.oanda.get_candles(
                instrument, tc.TREND_TIMEFRAME, tc.CANDLE_COUNT[tc.TREND_TIMEFRAME]
            )
            if daily_data is not None:
                mtf_data['daily'] = self.ta.add_moving_averages(daily_data)
                if tc.DEBUG_MODE:
                    print(f"✓ Daily data: {len(daily_data)} candles")
            
            # H4 data for zones
            h4_data = self.oanda.get_candles(
                instrument, tc.ZONE_TIMEFRAME, tc.CANDLE_COUNT[tc.ZONE_TIMEFRAME]
            )
            if h4_data is not None:
                mtf_data['h4'] = self.ta.add_moving_averages(h4_data)
                if tc.DEBUG_MODE:
                    print(f"✓ H4 data: {len(h4_data)} candles")
            
            # H1 data for execution
            h1_data = self.oanda.get_candles(
                instrument, tc.EXECUTION_TIMEFRAME, tc.CANDLE_COUNT[tc.EXECUTION_TIMEFRAME]
            )
            if h1_data is not None:
                mtf_data['h1'] = self.ta.add_moving_averages(h1_data)
                if tc.DEBUG_MODE:
                    print(f"✓ H1 data: {len(h1_data)} candles")
            
        except Exception as e:
            print(f"Error fetching multi-timeframe data: {e}")
        
        return mtf_data
    
    def analyze_trend_bias(self, daily_data: pd.DataFrame) -> Dict:
        """
        Analyze trend bias from higher timeframe (Daily)
        Returns trend direction and strength
        """
        if daily_data.empty:
            return {'bias': 'NEUTRAL', 'strength': 'WEAK'}
        
        trend_bias = self.ta.get_trend_bias(daily_data)
        
        # Additional trend strength analysis
        latest = daily_data.iloc[-1]
        
        # Check MA separation for trend strength
        fast_slow_separation = abs(latest['fast_ma'] - latest['slow_ma'])
        price_trend_separation = abs(latest['close'] - latest['trend_ma'])
        
        # Calculate ATR for relative strength measurement
        atr = self.ta.calculate_atr(daily_data).iloc[-1]
        
        if fast_slow_separation > atr * 0.5 and price_trend_separation > atr * 0.3:
            strength = 'STRONG'
        elif fast_slow_separation > atr * 0.2:
            strength = 'MEDIUM'
        else:
            strength = 'WEAK'
        
        return {
            'bias': trend_bias,
            'strength': strength,
            'fast_ma': latest['fast_ma'],
            'slow_ma': latest['slow_ma'],
            'trend_ma': latest['trend_ma'],
            'current_price': latest['close'],
            'atr': atr
        }
    
    def identify_zones(self, h4_data: pd.DataFrame) -> Dict:
        """
        Identify trading zones from H4 timeframe
        Returns zone data with interaction history
        """
        if h4_data.empty:
            return {}
        
        zones = self.ta.create_zones(h4_data, tc.ZONE_WIDTH_PIPS)
        zone_interactions = self.ta.get_zone_interaction(h4_data)
        
        # Enhance zones with interaction data
        for zone_name in ['fast_ma_zone', 'slow_ma_zone', 'trend_ma_zone']:
            if zone_name in zones:
                zone_key = zone_name.replace('_zone', '')
                zones[zone_name]['touches'] = zone_interactions.get(f"{zone_key}_touches", 0)
                zones[zone_name]['rejections'] = zone_interactions.get(f"{zone_key}_rejections", 0)
                zones[zone_name]['quality'] = self._assess_zone_quality(
                    zones[zone_name]['touches'], zones[zone_name]['rejections']
                )
        
        return zones
    
    def _assess_zone_quality(self, touches: int, rejections: int) -> str:
        """Assess zone quality based on interaction history"""
        if rejections >= 2 and touches >= tc.MIN_ZONE_TOUCHES:
            return 'HIGH'
        elif rejections >= 1 and touches >= tc.MIN_ZONE_TOUCHES:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def find_entry_signals(self, h1_data: pd.DataFrame, zones: Dict, trend_bias: Dict) -> Dict:
        """
        Find entry signals on H1 timeframe using price action within zones
        """
        if h1_data.empty or not zones:
            return {'signal': 'NO_SIGNAL', 'details': {}}
        
        # Analyze price action confluence
        confluence = self.pa.analyze_price_action_confluence(h1_data, zones)
        
        # Check if price is currently in a quality zone
        current_price = h1_data['close'].iloc[-1]
        in_zone = False
        active_zones = []
        
        for zone_name, zone_data in zones.items():
            if zone_data.get('quality') in ['HIGH', 'MEDIUM']:
                if self.ta.is_price_in_zone(current_price, zone_data):
                    in_zone = True
                    active_zones.append(zone_name)
        
        # Volume analysis
        volume_profile = self.ta.calculate_volume_profile(h1_data)
        
        # Generate trading signal
        signal_strength = self._calculate_signal_strength(
            confluence, trend_bias, in_zone, volume_profile, active_zones
        )
        
        return {
            'signal': signal_strength['signal'],
            'confidence': signal_strength['confidence'],
            'entry_price': current_price,
            'active_zones': active_zones,
            'confluence': confluence,
            'volume_profile': volume_profile,
            'trend_alignment': self._check_trend_alignment(confluence, trend_bias),
            'risk_reward': self._calculate_risk_reward(h1_data, zones, signal_strength['signal'])
        }
    
    def _calculate_signal_strength(self, confluence: Dict, trend_bias: Dict, 
                                 in_zone: bool, volume_profile: Dict, active_zones: List) -> Dict:
        """Calculate overall signal strength and direction"""
        
        base_confidence = 0
        signal = 'NO_SIGNAL'
        
        # Confluence contribution
        if confluence['signal'] in ['STRONG_BULLISH', 'STRONG_BEARISH']:
            base_confidence += 40
            signal = confluence['signal'].replace('STRONG_', '')
        elif confluence['signal'] in ['BULLISH', 'BEARISH']:
            base_confidence += 20
            signal = confluence['signal']
        
        # Zone quality contribution
        if in_zone:
            high_quality_zones = sum(1 for zone in active_zones 
                                   if zone in ['fast_ma_zone', 'slow_ma_zone'])
            base_confidence += high_quality_zones * 15
        
        # Trend alignment contribution
        if trend_bias['bias'] != 'NEUTRAL':
            if ((signal == 'BULLISH' and trend_bias['bias'] == 'BULLISH') or
                (signal == 'BEARISH' and trend_bias['bias'] == 'BEARISH')):
                base_confidence += 25 if trend_bias['strength'] == 'STRONG' else 15
            else:
                base_confidence -= 20  # Counter-trend penalty
        
        # Volume contribution
        if volume_profile.get('is_spike', False):
            base_confidence += 10
        
        # Final signal determination
        if base_confidence >= 70:
            final_signal = f'STRONG_{signal}'
        elif base_confidence >= 50:
            final_signal = signal
        elif base_confidence >= 30:
            final_signal = f'WEAK_{signal}'
        else:
            final_signal = 'NO_SIGNAL'
        
        return {
            'signal': final_signal,
            'confidence': min(base_confidence, 100)
        }
    
    def _check_trend_alignment(self, confluence: Dict, trend_bias: Dict) -> bool:
        """Check if signal aligns with higher timeframe trend"""
        signal = confluence['signal']
        bias = trend_bias['bias']
        
        if 'BULLISH' in signal and bias == 'BULLISH':
            return True
        elif 'BEARISH' in signal and bias == 'BEARISH':
            return True
        else:
            return False
    
    def _calculate_risk_reward(self, h1_data: pd.DataFrame, zones: Dict, signal: str) -> Dict:
        """Calculate risk-reward based on zones and ATR"""
        if 'NO_SIGNAL' in signal:
            return {'stop_loss': None, 'take_profit': None, 'risk_reward': None}
        
        current_price = h1_data['close'].iloc[-1]
        atr = self.ta.calculate_atr(h1_data, 14).iloc[-1]
        
        if 'BULLISH' in signal:
            # For bullish signals, stop below nearest support zone
            stop_loss = current_price - (atr * 2.5)  # Widened from 1.5 to 2.5
            take_profit = current_price + (atr * tc.RISK_REWARD_RATIO * 2.5)
        else:  # BEARISH
            # For bearish signals, stop above nearest resistance zone
            stop_loss = current_price + (atr * 2.5)  # Widened from 1.5 to 2.5
            take_profit = current_price - (atr * tc.RISK_REWARD_RATIO * 2.5)
        
        risk = abs(current_price - stop_loss)
        reward = abs(take_profit - current_price)
        rr_ratio = reward / risk if risk > 0 else 0
        
        return {
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward': rr_ratio,
            'risk_pips': risk / 0.0001,
            'reward_pips': reward / 0.0001
        }
    
    def plot_zone_analysis(self, mtf_data: Dict, zones: Dict, entry_signals: Dict, 
                          instrument: str = tc.DEFAULT_INSTRUMENT):
        """
        Plot comprehensive zone analysis chart
        """
        if not mtf_data or 'h1' not in mtf_data:
            print("Insufficient data for plotting")
            return
        
        # Check if charts are enabled in config
        import config
        if not config.SHOW_CHARTS:
            return
        
        h1_data = mtf_data['h1'].tail(100)  # Show last 100 H1 candles
        
        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(tc.CHART_WIDTH, tc.CHART_HEIGHT), 
                                       height_ratios=[3, 1])
        fig.patch.set_facecolor('#0e1217')
        
        # Main price chart
        self._plot_candlesticks(ax1, h1_data)
        self._plot_zones(ax1, zones, len(h1_data))
        self._plot_moving_averages(ax1, h1_data)
        self._plot_entry_signals(ax1, h1_data, entry_signals)
        
        # Volume chart
        if 'volume' in h1_data.columns:
            self._plot_volume(ax2, h1_data)
        
        # Chart styling
        ax1.set_title(f"{instrument} - Zone-Based Analysis (H1)", 
                     fontsize=16, color='white', fontweight='bold')
        ax1.set_ylabel("Price", fontsize=12, color='white')
        ax1.grid(True, alpha=0.3, color='#37474f')
        ax1.tick_params(colors='white')
        
        ax2.set_ylabel("Volume", fontsize=10, color='white')
        ax2.set_xlabel("Time", fontsize=12, color='white')
        ax2.grid(True, alpha=0.3, color='#37474f')
        ax2.tick_params(colors='white')
        
        # Format x-axis
        n_ticks = 8
        tick_positions = np.linspace(0, len(h1_data)-1, n_ticks, dtype=int)
        tick_labels = [h1_data.index[i].strftime('%m/%d %H:%M') for i in tick_positions]
        
        for ax in [ax1, ax2]:
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(tick_labels, rotation=45, ha='right', color='white')
            ax.set_xlim(-0.5, len(h1_data)-0.5)
        
        plt.tight_layout()
        plt.show()
        plt.style.use('default')
    
    def _plot_candlesticks(self, ax, df):
        """Plot candlesticks on given axis"""
        bull_color = '#26a69a'
        bear_color = '#ef5350'
        wick_color = '#b0bec5'
        
        for i, (timestamp, row) in enumerate(df.iterrows()):
            color = bull_color if row['close'] >= row['open'] else bear_color
            
            # Wicks
            ax.plot([i, i], [row['low'], row['high']], 
                   color=wick_color, linewidth=1, alpha=0.8)
            
            # Body
            body_height = abs(row['close'] - row['open'])
            body_bottom = min(row['open'], row['close'])
            
            if body_height > 0:
                rect = patches.Rectangle((i - 0.4, body_bottom), 0.8, body_height,
                                       facecolor=color, edgecolor=color, alpha=0.9)
                ax.add_patch(rect)
    
    def _plot_zones(self, ax, zones, data_length):
        """Plot trading zones as horizontal bands"""
        colors = {
            'fast_ma_zone': tc.BULLISH_ZONE_COLOR,
            'slow_ma_zone': tc.BEARISH_ZONE_COLOR,
            'trend_ma_zone': tc.NEUTRAL_ZONE_COLOR
        }
        
        for zone_name, zone_data in zones.items():
            if zone_data.get('quality') in ['HIGH', 'MEDIUM']:
                color = colors.get(zone_name, '#888888')
                alpha = 0.3 if zone_data['quality'] == 'HIGH' else 0.2
                
                ax.axhspan(zone_data['lower'], zone_data['upper'], 
                          color=color, alpha=alpha, label=f"{zone_name} ({zone_data['quality']})")
    
    def _plot_moving_averages(self, ax, df):
        """Plot moving averages"""
        x_range = range(len(df))
        ax.plot(x_range, df['fast_ma'], color='#FFA726', linewidth=2, alpha=0.8, label=f'Fast MA ({tc.FAST_MA_PERIOD})')
        ax.plot(x_range, df['slow_ma'], color='#EF5350', linewidth=2, alpha=0.8, label=f'Slow MA ({tc.SLOW_MA_PERIOD})')
        ax.plot(x_range, df['trend_ma'], color='#42A5F5', linewidth=2, alpha=0.8, label=f'Trend MA ({tc.TREND_MA_PERIOD})')
        ax.legend(loc='upper left', fontsize=8)
    
    def _plot_entry_signals(self, ax, df, signals):
        """Plot entry signals on chart"""
        if signals['signal'] == 'NO_SIGNAL':
            return
        
        latest_idx = len(df) - 1
        latest_price = df['close'].iloc[-1]
        
        if 'BULLISH' in signals['signal']:
            ax.scatter(latest_idx, latest_price, color='lime', s=200, marker='^', 
                      zorder=5, label=f"BUY - {signals['confidence']}%")
        elif 'BEARISH' in signals['signal']:
            ax.scatter(latest_idx, latest_price, color='red', s=200, marker='v', 
                      zorder=5, label=f"SELL - {signals['confidence']}%")
        
        # Plot stop loss and take profit levels
        if signals['risk_reward']['stop_loss']:
            ax.axhline(signals['risk_reward']['stop_loss'], color='red', linestyle='--', alpha=0.7, label='Stop Loss')
        if signals['risk_reward']['take_profit']:
            ax.axhline(signals['risk_reward']['take_profit'], color='lime', linestyle='--', alpha=0.7, label='Take Profit')
    
    def _plot_volume(self, ax, df):
        """Plot volume bars"""
        if 'volume' not in df.columns:
            return
        
        bull_color = '#26a69a'
        bear_color = '#ef5350'
        
        colors = [bull_color if df.iloc[i]['close'] >= df.iloc[i]['open'] 
                 else bear_color for i in range(len(df))]
        
        ax.bar(range(len(df)), df['volume'], color=colors, alpha=0.6)
    
    def run_analysis(self, instrument: str = tc.DEFAULT_INSTRUMENT) -> Dict:
        """
        Run complete zone-based trading analysis
        Returns comprehensive analysis results
        """
        print(f"\n{'='*60}")
        print(f"ZONE TRADER ANALYSIS - {instrument}")
        print(f"{'='*60}")
        
        # Get multi-timeframe data
        mtf_data = self.get_multi_timeframe_data(instrument)
        
        if not mtf_data:
            print("❌ Failed to fetch required data")
            return {}
        
        # Analyze trend bias from daily
        print(f"\n📈 TREND ANALYSIS ({tc.TREND_TIMEFRAME})")
        trend_analysis = self.analyze_trend_bias(mtf_data.get('daily', pd.DataFrame()))
        print(f"Trend Bias: {trend_analysis['bias']} ({trend_analysis['strength']})")
        print(f"Current Price: {trend_analysis['current_price']:.5f}")
        print(f"Fast MA: {trend_analysis['fast_ma']:.5f}")
        print(f"Slow MA: {trend_analysis['slow_ma']:.5f}")
        
        # Identify zones from H4
        print(f"\n🎯 ZONE ANALYSIS ({tc.ZONE_TIMEFRAME})")
        zones = self.identify_zones(mtf_data.get('h4', pd.DataFrame()))
        for zone_name, zone_data in zones.items():
            print(f"{zone_name}: {zone_data['lower']:.5f} - {zone_data['upper']:.5f} "
                  f"({zone_data['quality']} quality, {zone_data['touches']} touches)")
        
        # Find entry signals from H1
        print(f"\n⚡ ENTRY SIGNALS ({tc.EXECUTION_TIMEFRAME})")
        entry_signals = self.find_entry_signals(
            mtf_data.get('h1', pd.DataFrame()), zones, trend_analysis
        )
        
        print(f"Signal: {entry_signals['signal']}")
        print(f"Confidence: {entry_signals['confidence']}%")
        print(f"Trend Aligned: {entry_signals['trend_alignment']}")
        
        if entry_signals['risk_reward']['risk_reward']:
            print(f"Risk/Reward: 1:{entry_signals['risk_reward']['risk_reward']:.2f}")
            print(f"Stop Loss: {entry_signals['risk_reward']['stop_loss']:.5f}")
            print(f"Take Profit: {entry_signals['risk_reward']['take_profit']:.5f}")
        
        # Plot analysis
        if mtf_data:
            self.plot_zone_analysis(mtf_data, zones, entry_signals, instrument)
        
        return {
            'instrument': instrument,
            'trend_analysis': trend_analysis,
            'zones': zones,
            'entry_signals': entry_signals,
            'mtf_data': mtf_data
        }

def main():
    """Main function to run zone trader analysis"""
    trader = ZoneTrader()
    
    # Run analysis for default instrument
    results = trader.run_analysis(tc.DEFAULT_INSTRUMENT)
    
    # Optionally analyze multiple pairs
    if tc.DEBUG_MODE and len(tc.MAJOR_PAIRS) > 1:
        print(f"\n{'='*60}")
        print("MULTI-PAIR SCAN")
        print(f"{'='*60}")
        
        for pair in tc.MAJOR_PAIRS[:3]:  # Limit to first 3 pairs to avoid rate limits
            if pair != tc.DEFAULT_INSTRUMENT:
                print(f"\n--- {pair} ---")
                try:
                    pair_results = trader.run_analysis(pair)
                    if pair_results.get('entry_signals', {}).get('signal') != 'NO_SIGNAL':
                        print(f"🎯 {pair}: {pair_results['entry_signals']['signal']} "
                              f"({pair_results['entry_signals']['confidence']}%)")
                except Exception as e:
                    print(f"❌ Error analyzing {pair}: {e}")

if __name__ == "__main__":
    main()