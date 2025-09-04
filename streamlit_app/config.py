# Configuration file for Streamlit deployment
# Uses Streamlit secrets management for API keys

import streamlit as st
import os

# Get OANDA access token from Streamlit secrets or environment variable
try:
    # Try to get from Streamlit secrets first
    OANDA_ACCESS_TOKEN = st.secrets["OANDA_ACCESS_TOKEN"]
except:
    # Fallback to environment variable for local development
    OANDA_ACCESS_TOKEN = os.getenv("OANDA_ACCESS_TOKEN", "")
    if not OANDA_ACCESS_TOKEN:
        st.error("❌ OANDA_ACCESS_TOKEN not found in secrets or environment variables")
        st.info("Please set up your API key in Streamlit secrets or environment variables")

# Chart display settings - disabled by default for web deployment
SHOW_CHARTS = False  # Set to True to enable chart display, False to disable

# Additional Streamlit-specific settings
STREAMLIT_DEPLOYMENT = True

# Email notification settings
try:
    # Email configuration from Streamlit secrets
    SENDER_EMAIL = st.secrets.get("SENDER_EMAIL", "")
    SENDER_PASSWORD = st.secrets.get("SENDER_PASSWORD", "")
    RECIPIENT_EMAIL = st.secrets.get("RECIPIENT_EMAIL", "")
except:
    # Fallback to environment variables for local development
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
    RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "")

# Trading session settings
TRADING_SESSIONS = {
    # Format: (start_hour_utc, end_hour_utc)
    "SYDNEY": (21, 6),      # 21:00 UTC - 06:00 UTC next day
    "TOKYO": (23, 8),       # 23:00 UTC - 08:00 UTC next day  
    "LONDON": (7, 16),      # 07:00 UTC - 16:00 UTC
    "NEW_YORK": (12, 21)    # 12:00 UTC - 21:00 UTC
}

# Currency pair to trading session mapping
# Pairs are most liquid during their respective regional sessions
PAIR_TRADING_SESSIONS = {
    "EUR_USD": ["LONDON", "NEW_YORK"],      # Most active during European and US sessions
    "GBP_USD": ["LONDON", "NEW_YORK"],      # Most active during European and US sessions
    "USD_JPY": ["TOKYO", "LONDON"],         # Most active during Asian and European sessions
    "AUD_USD": ["SYDNEY", "TOKYO"],         # Most active during Pacific and Asian sessions
    "USD_CAD": ["NEW_YORK"],                # Most active during US session
    "NZD_USD": ["SYDNEY", "TOKYO"],         # Most active during Pacific and Asian sessions
    "GBP_JPY": ["TOKYO", "LONDON"],         # Most active during Asian and European sessions
    "EUR_GBP": ["LONDON"],                  # Most active during European session
    "USD_CHF": ["LONDON", "NEW_YORK"],      # Most active during European and US sessions
    "EUR_JPY": ["TOKYO", "LONDON"],         # Most active during Asian and European sessions
}

def is_pair_in_trading_session(pair):
    """
    Check if a currency pair is currently in an active trading session
    Returns (is_active, session_info)
    """
    from datetime import datetime, timezone
    
    if pair not in PAIR_TRADING_SESSIONS:
        return True, "Unknown pair - trading allowed"
    
    current_utc = datetime.now(timezone.utc)
    current_hour = current_utc.hour
    
    active_sessions = []
    
    for session_name in PAIR_TRADING_SESSIONS[pair]:
        start_hour, end_hour = TRADING_SESSIONS[session_name]
        
        # Handle sessions that cross midnight UTC
        if start_hour > end_hour:
            is_active = current_hour >= start_hour or current_hour < end_hour
        else:
            is_active = start_hour <= current_hour < end_hour
            
        if is_active:
            active_sessions.append(session_name)
    
    if active_sessions:
        return True, f"Active sessions: {', '.join(active_sessions)}"
    else:
        # Find next active session
        next_sessions = []
        for session_name in PAIR_TRADING_SESSIONS[pair]:
            start_hour, _ = TRADING_SESSIONS[session_name]
            if start_hour > current_hour:
                hours_until = start_hour - current_hour
            else:
                hours_until = (24 - current_hour) + start_hour
            next_sessions.append((session_name, hours_until))
        
        if next_sessions:
            next_session = min(next_sessions, key=lambda x: x[1])
            return False, f"Next active session: {next_session[0]} (in {next_session[1]}h)"
        else:
            return False, "No active trading sessions"