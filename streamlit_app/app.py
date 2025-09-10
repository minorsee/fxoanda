#!/usr/bin/env python3
"""
Streamlit Live Trading Signals Dashboard
"""

import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from email_notifications import EmailNotifier
from config import is_pair_in_trading_session

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set page config
st.set_page_config(
    page_title="Live Trading Signals",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.big-font {
    font-size: 24px !important;
    font-weight: bold;
}
.metric-card {
    background-color: #f0f2f6;
    padding: 10px;
    border-radius: 10px;
    margin: 5px 0;
}
.signal-bullish {
    color: #26a69a;
    font-weight: bold;
}
.signal-bearish {
    color: #ef5350;
    font-weight: bold;
}
.signal-neutral {
    color: #757575;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_live_signals_data(instrument="USD_JPY"):
    """Get current trading signals for an instrument with safe NaN handling"""
    
    try:
        # Use safe analysis wrapper to prevent NaN warnings
        from safe_analysis import safe_get_signals
        
        # Get signals with NaN protection
        results = safe_get_signals(instrument)
        
        if not results:
            return None
        
        return results
        
    except Exception as e:
        st.error(f"❌ Error getting signals: {e}")
        return None

def create_price_chart(mtf_data, instrument):
    """Create interactive price chart using Plotly"""
    
    if not mtf_data or 'h1' not in mtf_data:
        return None
    
    df = mtf_data['h1'].tail(100)  # Last 100 H1 candles
    
    # Create candlestick chart
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=[f"{instrument} - H1 Chart", "Volume"],
        row_width=[0.7, 0.3]
    )
    
    # Add candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="Price",
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ),
        row=1, col=1
    )
    
    # Add moving averages if available
    if 'fast_ma' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['fast_ma'],
                name="Fast MA",
                line=dict(color='yellow', width=1)
            ),
            row=1, col=1
        )
    
    if 'slow_ma' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['slow_ma'],
                name="Slow MA",
                line=dict(color='blue', width=1)
            ),
            row=1, col=1
        )
    
    # Add volume if available
    if 'volume' in df.columns and df['volume'].sum() > 0:
        colors = ['#26a69a' if close >= open else '#ef5350' 
                 for close, open in zip(df['close'], df['open'])]
        
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['volume'],
                name="Volume",
                marker_color=colors,
                opacity=0.7
            ),
            row=2, col=1
        )
    
    # Update layout
    fig.update_layout(
        title=f"{instrument} Live Analysis",
        xaxis_title="Time",
        yaxis_title="Price",
        template="plotly_dark",
        height=600,
        showlegend=True
    )
    
    fig.update_xaxes(rangeslider_visible=False)
    
    return fig

def display_signal_card(signal, confidence, entry_signals):
    """Display signal information in a card format with safe number formatting"""
    from safe_analysis import safe_format_number, safe_format_percentage
    
    if signal == 'NO_SIGNAL':
        st.markdown('<div class="signal-neutral">⏳ NO SIGNAL</div>', unsafe_allow_html=True)
        st.write(f"Confidence: {confidence}%")
        return
    
    # Signal direction
    direction = "🚀 BUY" if 'BULLISH' in signal else "🔻 SELL"
    signal_class = "signal-bullish" if 'BULLISH' in signal else "signal-bearish"
    
    st.markdown(f'<div class="{signal_class}">{direction}</div>', unsafe_allow_html=True)
    
    # Main trade metrics in 4 columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Confidence", safe_format_percentage(confidence))
    
    with col2:
        if entry_signals.get('entry_price'):
            entry_price = safe_format_number(entry_signals['entry_price'])
            st.markdown("**📍 Entry Price**")
            st.markdown(f'<div style="font-size: 20px; font-weight: bold; color: #1f77b4;">{entry_price}</div>', 
                       unsafe_allow_html=True)
    
    with col3:
        rr = entry_signals.get('risk_reward', {})
        if rr.get('take_profit'):
            tp_price = safe_format_number(rr['take_profit'])
            st.markdown("**🎯 Take Profit**")
            st.markdown(f'<div style="font-size: 20px; font-weight: bold; color: #26a69a;">{tp_price}</div>', 
                       unsafe_allow_html=True)
    
    with col4:
        rr = entry_signals.get('risk_reward', {})
        if rr.get('stop_loss'):
            sl_price = safe_format_number(rr['stop_loss'])
            st.markdown("**🛑 Stop Loss**")
            st.markdown(f'<div style="font-size: 20px; font-weight: bold; color: #ef5350;">{sl_price}</div>', 
                       unsafe_allow_html=True)
    
    # Additional risk/reward info
    if rr.get('risk_reward'):
        st.info(f"**Risk:Reward Ratio:** 1:{safe_format_number(rr['risk_reward'], 2)}")
        
        # Calculate pips if available
        if rr.get('risk_pips') and rr.get('reward_pips'):
            st.caption(f"Risk: {safe_format_number(rr['risk_pips'], 1)} pips | Reward: {safe_format_number(rr['reward_pips'], 1)} pips")

def display_trade_details(entry_signals, results):
    """Display detailed trade information with safe formatting"""
    from safe_analysis import safe_format_number, safe_format_percentage
    
    rr = entry_signals.get('risk_reward', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Trade Setup")
        if rr.get('stop_loss'):
            st.write(f"**Stop Loss:** {safe_format_number(rr['stop_loss'])}")
        if rr.get('take_profit'):
            st.write(f"**Take Profit:** {safe_format_number(rr['take_profit'])}")
        
        # Trend alignment
        trend_aligned = entry_signals.get('trend_alignment', False)
        alignment_icon = "✅" if trend_aligned else "❌"
        st.write(f"**Trend Aligned:** {alignment_icon}")
    
    with col2:
        st.subheader("🎯 Analysis")
        trend_analysis = results.get('trend_analysis', {})
        st.write(f"**Trend Bias:** {trend_analysis.get('bias', 'N/A')}")
        st.write(f"**Trend Strength:** {trend_analysis.get('strength', 'N/A')}")
        st.write(f"**Active Zones:** {len(entry_signals.get('active_zones', []))}")
        
        # Volume info
        volume_profile = entry_signals.get('volume_profile', {})
        if volume_profile.get('is_spike'):
            st.write(f"**Volume:** 🔥 SPIKE ({safe_format_number(volume_profile.get('volume_ratio', 0), 1)}x avg)")

def display_multi_pair_signals(email_notifier=None):
    """Display signals for multiple currency pairs with safe number formatting"""
    from safe_analysis import safe_format_number, safe_format_percentage
    
    pairs = ["EUR_USD", "GBP_USD", "AUD_USD", "NZD_USD"]  # Keep to 4 main pairs
    
    st.subheader("🌍 Multi-Pair Signal Scan")
    
    # Add cache status and controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.caption(f"Scanning {len(pairs)} pairs (auto-batched to respect rate limits)")
    
    with col2:
        if st.button("📦 Cache Status"):
            try:
                from rate_limited_fetcher import get_cache_status
                cache_info = get_cache_status()
                st.info(f"Cached: {cache_info['valid_entries']} pairs, Duration: {cache_info['cache_duration_minutes']:.0f}m")
            except:
                st.info("Cache status unavailable")
    
    with col3:
        if st.button("🗑️ Clear Cache"):
            try:
                from rate_limited_fetcher import clear_data_cache
                clear_data_cache()
                st.success("Cache cleared!")
                st.rerun()
            except:
                st.error("Cache clear failed")
    
    # Add trading session info
    current_time = datetime.now()
    st.caption(f"Current UTC Time: {current_time.strftime('%H:%M')} | Only scanning pairs during active trading sessions")
    
    # Display trading session status
    with st.expander("🌐 Trading Session Status", expanded=False):
        session_cols = st.columns(4)
        sessions = ["SYDNEY", "TOKYO", "LONDON", "NEW_YORK"]
        
        from config import TRADING_SESSIONS
        current_hour = current_time.hour
        
        for i, session in enumerate(sessions):
            with session_cols[i]:
                start_hour, end_hour = TRADING_SESSIONS[session]
                
                # Check if session is active
                if start_hour > end_hour:  # Cross midnight
                    is_session_active = current_hour >= start_hour or current_hour < end_hour
                else:
                    is_session_active = start_hour <= current_hour < end_hour
                
                status_emoji = "🟢" if is_session_active else "🔴"
                st.markdown(f"{status_emoji} **{session}**")
                
                # Convert UTC hours to local time display
                if start_hour > end_hour:
                    time_range = f"{start_hour:02d}:00 - {end_hour:02d}:00+1"
                else:
                    time_range = f"{start_hour:02d}:00 - {end_hour:02d}:00"
                st.caption(f"UTC: {time_range}")
    
    # Create columns for pairs (use 4 columns, 2 rows for better layout)
    pairs_per_row = 4
    num_rows = (len(pairs) + pairs_per_row - 1) // pairs_per_row  # Ceiling division
    
    opportunities = []
    
    # Display pairs in rows of 4
    for row in range(num_rows):
        cols = st.columns(pairs_per_row)
        start_idx = row * pairs_per_row
        end_idx = min(start_idx + pairs_per_row, len(pairs))
        
        for col_idx, pair_idx in enumerate(range(start_idx, end_idx)):
            pair = pairs[pair_idx]
            with cols[col_idx]:
                try:
                    # Check trading session first
                    is_active, session_info = is_pair_in_trading_session(pair)
                    
                    st.markdown(f"**{pair}**")
                    
                    if not is_active:
                        # Pair not in active trading session
                        st.markdown('🕒 **CLOSED**')
                        st.caption(session_info)
                        continue
                        
                    # Show active session info
                    st.caption(session_info)
                    
                    results = get_live_signals_data(pair)
                    
                    if results:
                        entry_signals = results.get('entry_signals', {})
                        signal = entry_signals.get('signal', 'NO_SIGNAL')
                        confidence = entry_signals.get('confidence', 0)
                        
                        # Status indicator
                        if confidence >= 60:
                            status = "🎯"
                            status_color = "green"
                            
                            # Send email notification if enabled and signal is present
                            if email_notifier and signal != 'NO_SIGNAL':
                                rr = entry_signals.get('risk_reward', {})
                                success, message = email_notifier.send_signal_notification(
                                    pair=pair,
                                    signal=signal,
                                    confidence=confidence,
                                    entry_price=entry_signals.get('entry_price', 0),
                                    take_profit=rr.get('take_profit'),
                                    stop_loss=rr.get('stop_loss')
                                )
                                if success:
                                    st.sidebar.success(f"📧 Email sent for {pair}")
                                elif "already sent" not in message:
                                    st.sidebar.warning(f"📧 Email failed for {pair}: {message}")
                                
                        elif confidence >= 50:
                            status = "⚠️"
                            status_color = "orange"
                        else:
                            status = "⏳"
                            status_color = "gray"
                        
                        st.markdown(f'<span style="color: {status_color}">{status} {confidence}%</span>', 
                                   unsafe_allow_html=True)
                        
                        if signal != 'NO_SIGNAL':
                            direction = "BUY" if "BULLISH" in signal else "SELL"
                            st.write(f"{direction}")
                            
                            if confidence >= 50:
                                opportunities.append({
                                    'pair': pair,
                                    'signal': signal,
                                    'confidence': confidence,
                                    'entry_price': entry_signals.get('entry_price', 0),
                                    'trend_aligned': entry_signals.get('trend_alignment', False)
                                })
                        else:
                            st.write("NO SIGNAL")
                    
                except Exception as e:
                    st.write(f"❌ Error")
                    st.caption(str(e)[:20] + "...")
    
    # Show best opportunities with detailed info
    if opportunities:
        st.subheader("🏆 Best Opportunities")
        opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        
        for opp in opportunities[:3]:  # Top 3
            direction = "BUY" if "BULLISH" in opp['signal'] else "SELL"
            trend_emoji = "✅" if opp['trend_aligned'] else "❌"
            
            # Get additional trade details
            results = get_live_signals_data(opp['pair'])
            if results:
                entry_signals = results.get('entry_signals', {})
                rr = entry_signals.get('risk_reward', {})
                
                # Format full precision values
                entry_full = safe_format_number(opp['entry_price'])
                confidence_formatted = safe_format_percentage(opp['confidence'])
                
                with st.expander(f"🎯 {opp['pair']}: {direction} @ {entry_full} ({confidence_formatted} confidence) {trend_emoji}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f"**📍 Entry Price**")
                        st.code(safe_format_number(opp['entry_price']))
                    
                    with col2:
                        if rr.get('take_profit'):
                            st.markdown(f"**🎯 Take Profit**")
                            st.code(safe_format_number(rr['take_profit']))
                    
                    with col3:
                        if rr.get('stop_loss'):
                            st.markdown(f"**🛑 Stop Loss**")
                            st.code(safe_format_number(rr['stop_loss']))
                    
                    if rr.get('risk_reward'):
                        st.caption(f"Risk:Reward = 1:{safe_format_number(rr['risk_reward'], 2)}")
            else:
                entry_formatted = safe_format_number(opp['entry_price'])
                st.info(f"**{opp['pair']}:** {direction} @ {entry_formatted} "
                       f"({safe_format_percentage(opp['confidence'])} confidence) {trend_emoji}")

def health_check():
    """Health check endpoint to keep app alive"""
    # Check if health check is requested via query params
    query_params = st.query_params
    
    if 'health' in query_params:
        # Return JSON-like response for health check
        st.json({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'app_version': '1.0.0',
            'uptime': 'active'
        })
        st.stop()  # Stop execution after health check

def main():
    """Main Streamlit app with safe number formatting"""
    from safe_analysis import safe_format_number, safe_format_percentage
    
    # Handle health check first
    health_check()
    
    # Header
    st.title("📈 Live Trading Signals Dashboard")
    st.markdown("Real-time forex trading signals powered by zone-based analysis")
    
    # Current time display
    current_time = datetime.now()
    current_utc = datetime.utcnow()
    col1, col2 = st.columns([1, 1])
    with col1:
        st.info(f"🕒 **Local Time:** {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    with col2:
        st.info(f"🌍 **UTC Time:** {current_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Sidebar
    st.sidebar.title("⚙️ Settings")
    
    # Instrument selection
    instruments = ["EUR_USD", "GBP_USD", "AUD_USD", "NZD_USD"]  # XXX_USD pairs only
    
    selected_instrument = st.sidebar.selectbox(
        "Select Currency Pair",
        instruments,
        index=2  # Default to USD_JPY
    )
    
    # Display options
    show_chart = st.sidebar.checkbox("Show Chart", value=True)
    show_multi_pairs = st.sidebar.checkbox("Show Multi-Pair Scan", value=True)
    
    # Auto-refresh settings
    auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=False)
    
    if auto_refresh:
        refresh_interval = st.sidebar.slider(
            "Refresh Interval (seconds)",
            min_value=5,
            max_value=300,
            value=30,
            step=5,
            help="How often to refresh the data automatically"
        )
        st.sidebar.info(f"Auto-refreshing every {refresh_interval} seconds")
    else:
        refresh_interval = 30  # Default value when not auto-refreshing
    
    # Email notification settings
    st.sidebar.markdown("---")
    st.sidebar.subheader("📧 Email Notifications")
    
    enable_email_notifications = st.sidebar.checkbox(
        "Enable Email Alerts", 
        value=True,
        help="Send email when any pair exceeds 60% confidence"
    )
    
    if enable_email_notifications:
        st.sidebar.info("📧 Emails will be sent for signals with 60%+ confidence")
        
        # Test email configuration
        if st.sidebar.button("🧪 Test Email Config"):
            notifier = EmailNotifier()
            success, message = notifier.test_email_connection()
            if success:
                st.sidebar.success(f"✅ {message}")
            else:
                st.sidebar.error(f"❌ {message}")
                st.sidebar.info("Set email credentials in Streamlit secrets: SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL")
        
    # Initialize email notifier if enabled with session state persistence
    email_notifier = None
    if enable_email_notifications:
        # Initialize session state for sent signals if not exists
        if 'sent_signals' not in st.session_state:
            st.session_state.sent_signals = {}
        
        email_notifier = EmailNotifier()
        # Restore sent signals state from session state
        email_notifier.sent_signals = st.session_state.sent_signals
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Main content
    st.markdown("---")
    
    # Single pair analysis
    st.header(f"🎯 {selected_instrument} Analysis")
    
    # Get live signals
    with st.spinner(f"Fetching signals for {selected_instrument}..."):
        results = get_live_signals_data(selected_instrument)
    
    if results:
        entry_signals = results.get('entry_signals', {})
        signal = entry_signals.get('signal', 'NO_SIGNAL')
        confidence = entry_signals.get('confidence', 0)
        
        # Display main signal
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("🚨 Current Signal")
            display_signal_card(signal, confidence, entry_signals)
        
        with col2:
            if signal != 'NO_SIGNAL' and confidence >= 60:
                display_trade_details(entry_signals, results)
                
                # Send email notification if enabled
                if email_notifier:
                    rr = entry_signals.get('risk_reward', {})
                    success, message = email_notifier.send_signal_notification(
                        pair=selected_instrument,
                        signal=signal,
                        confidence=confidence,
                        entry_price=entry_signals.get('entry_price', 0),
                        take_profit=rr.get('take_profit'),
                        stop_loss=rr.get('stop_loss')
                    )
                    if success:
                        st.success(f"📧 Email notification sent!")
                    elif "already sent" not in message:
                        st.warning(f"📧 Email notification failed: {message}")
                        
            elif signal != 'NO_SIGNAL':
                st.warning(f"⚠️ Signal present but low confidence ({confidence}%)")
                st.info("Wait for higher confidence (60%+) before trading")
            else:
                st.info("⏳ No trading opportunity right now")
                trend_analysis = results.get('trend_analysis', {})
                st.write(f"**Current Trend:** {trend_analysis.get('bias', 'N/A')}")
                
                # Only show current price if it's valid (not 0.0)
                current_price = trend_analysis.get('current_price', 0)
                if current_price > 0:
                    st.write(f"**Current Price:** {safe_format_number(current_price)}")
                else:
                    st.write("**Current Price:** N/A (Data fetch error)")
        
        # Display chart if enabled
        if show_chart:
            st.markdown("---")
            st.subheader("📊 Price Chart")
            
            mtf_data = results.get('mtf_data', {})
            if mtf_data:
                chart = create_price_chart(mtf_data, selected_instrument)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
            else:
                st.warning("Chart data not available")
    
    else:
        st.error("❌ Unable to fetch signals. Please check your configuration.")
    
    # Multi-pair analysis
    if show_multi_pairs:
        st.markdown("---")
        display_multi_pair_signals(email_notifier)
    
    # Footer
    st.markdown("---")
    
    if auto_refresh:
        # Show countdown and auto-refresh
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        with col2:
            # Create a placeholder for countdown
            countdown_placeholder = st.empty()
        
        with col3:
            # Stop button
            if st.button("⏹️ Stop Auto-Refresh"):
                st.stop()
        
        # Countdown timer
        for i in range(refresh_interval, 0, -1):
            countdown_placeholder.markdown(f"*Refreshing in {i}s*")
            time.sleep(1)
        
        countdown_placeholder.markdown("*Refreshing now...*")
        st.rerun()
        
    else:
        st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

if __name__ == "__main__":
    main()