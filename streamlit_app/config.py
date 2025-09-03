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