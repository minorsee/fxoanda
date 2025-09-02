import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta
import config
import numpy as np

class OandaTrader:
    def __init__(self):
        self.api = oandapyV20.API(
            access_token=config.OANDA_ACCESS_TOKEN,
        )
    
    def get_candles(self, instrument="EUR_USD", granularity="D", count=100):
        """
        Fetch candle data from OANDA API
        
        Args:
            instrument (str): Currency pair (e.g., "EUR_USD")
            granularity (str): Timeframe - "D" (daily), "H4" (4-hour), "H1" (1-hour)
            count (int): Number of candles to fetch (max 5000)
        
        Returns:
            pandas.DataFrame: OHLC data with datetime index
        """
        params = {
            "count": count,
            "granularity": granularity
        }
        
        r = instruments.InstrumentsCandles(instrument=instrument, params=params)
        
        try:
            response = self.api.request(r)
            candles = response['candles']
            
            data = []
            for candle in candles:
                if candle['complete']:
                    data.append({
                        'time': candle['time'],
                        'open': float(candle['mid']['o']),
                        'high': float(candle['mid']['h']),
                        'low': float(candle['mid']['l']),
                        'close': float(candle['mid']['c']),
                        'volume': int(candle['volume'])
                    })
            
            df = pd.DataFrame(data)
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    def plot_chart(self, df, instrument="EUR_USD", timeframe="Daily"):
        """
        Plot professional OHLC candlestick chart
        
        Args:
            df (pandas.DataFrame): OHLC data
            instrument (str): Currency pair name for title
            timeframe (str): Timeframe for title
        """
        if df is None or df.empty:
            print("No data to plot")
            return
        
        # Check if charts are enabled in config
        if not config.SHOW_CHARTS:
            return
        
        # Set style for professional look
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(15, 8))
        fig.patch.set_facecolor('#0e1217')
        ax.set_facecolor('#0e1217')
        
        # Calculate candle width based on timeframe
        if timeframe == "Daily":
            width = 0.6
        elif timeframe == "H4":
            width = 0.15
        else:  # H1
            width = 0.04
        
        # Colors for bullish and bearish candles
        bull_color = '#26a69a'  # Teal green
        bear_color = '#ef5350'  # Red
        wick_color = '#b0bec5'  # Light gray
        
        # Plot candlesticks
        for i, (timestamp, row) in enumerate(df.iterrows()):
            is_bullish = row['close'] >= row['open']
            color = bull_color if is_bullish else bear_color
            
            # Plot wicks first (so they appear behind the body)
            ax.plot([i, i], [row['low'], row['high']], 
                   color=wick_color, linewidth=1, alpha=0.8)
            
            # Plot body
            body_height = abs(row['close'] - row['open'])
            body_bottom = min(row['open'], row['close'])
            
            if body_height > 0:  # Normal candle
                rect = Rectangle((i - width/2, body_bottom), width, body_height,
                               facecolor=color, edgecolor=color, alpha=0.9)
                ax.add_patch(rect)
            else:  # Doji (open == close)
                ax.plot([i - width/2, i + width/2], [row['open'], row['close']], 
                       color=color, linewidth=2)
        
        # Styling
        ax.set_title(f"{instrument} - {timeframe} Chart", 
                    fontsize=16, color='white', fontweight='bold', pad=20)
        ax.set_ylabel("Price", fontsize=12, color='white')
        ax.set_xlabel("Time", fontsize=12, color='white')
        
        # Grid
        ax.grid(True, alpha=0.3, color='#37474f')
        ax.set_axisbelow(True)
        
        # Format x-axis with proper timestamps
        n_ticks = min(10, len(df))
        tick_positions = np.linspace(0, len(df)-1, n_ticks, dtype=int)
        tick_labels = [df.index[i].strftime('%m/%d %H:%M') if timeframe in ['H1', 'H4'] 
                      else df.index[i].strftime('%Y-%m-%d') for i in tick_positions]
        
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels, rotation=45, ha='right', color='white')
        ax.set_xlim(-0.5, len(df)-0.5)
        
        # Y-axis formatting
        ax.tick_params(colors='white')
        
        # Add volume subplot (optional)
        if 'volume' in df.columns and df['volume'].sum() > 0:
            # Create volume subplot
            ax2 = ax.twinx()
            volume_colors = [bull_color if df.iloc[i]['close'] >= df.iloc[i]['open'] 
                           else bear_color for i in range(len(df))]
            ax2.bar(range(len(df)), df['volume'], color=volume_colors, alpha=0.7, width=0.8)
            ax2.set_ylabel('Volume', color='white', fontweight='bold')
            ax2.tick_params(colors='white')
            ax2.set_ylim(0, df['volume'].max() * 1.2)
            
            # Format volume numbers to be more readable
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K' if x >= 1000 else f'{x:.0f}'))
        
        plt.tight_layout()
        plt.show()
        
        # Reset to default style after plotting
        plt.style.use('default')
    
    def get_daily_data(self, instrument="EUR_USD", count=100):
        """Get daily candle data"""
        return self.get_candles(instrument, "D", count)
    
    def get_h4_data(self, instrument="EUR_USD", count=100):
        """Get 4-hour candle data"""
        return self.get_candles(instrument, "H4", count)
    
    def get_h1_data(self, instrument="EUR_USD", count=100):
        """Get 1-hour candle data"""
        return self.get_candles(instrument, "H1", count)

def main():
    # Initialize trader
    trader = OandaTrader()
    
    instrument = "EUR_USD"
    
    print(f"Fetching data for {instrument}...")
    
    # Get daily data
    print("Fetching daily data...")
    daily_data = trader.get_daily_data(instrument, 50)
    if daily_data is not None:
        print(f"Daily data shape: {daily_data.shape}")
        print(daily_data.head())
        trader.plot_chart(daily_data, instrument, "Daily")
    
    # Get H4 data
    print("Fetching H4 data...")
    h4_data = trader.get_h4_data(instrument, 100)
    if h4_data is not None:
        print(f"H4 data shape: {h4_data.shape}")
        print(h4_data.head())
        trader.plot_chart(h4_data, instrument, "H4")
    
    # Get H1 data
    print("Fetching H1 data...")
    h1_data = trader.get_h1_data(instrument, 100)
    if h1_data is not None:
        print(f"H1 data shape: {h1_data.shape}")
        print(h1_data.head())
        trader.plot_chart(h1_data, instrument, "H1")

if __name__ == "__main__":
    main()