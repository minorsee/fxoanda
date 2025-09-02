# Live Trading Signals - Streamlit Dashboard

A real-time forex trading signals dashboard built with Streamlit, featuring multi-timeframe zone-based analysis.

## Features

- 📈 **Real-time Signals**: Live trading signals for major forex pairs
- 🎯 **Multi-Pair Analysis**: Monitor multiple currency pairs simultaneously  
- 📊 **Interactive Charts**: Plotly-powered candlestick charts with technical indicators
- ⚡ **Auto-Refresh**: Optional auto-refresh functionality
- 🔒 **Secure**: API keys managed through Streamlit secrets

## Deployment on Streamlit Cloud

### 1. Prepare Your Repository
- Push this `streamlit_app` folder to your GitHub repository
- Make sure `.streamlit/secrets.toml` is in your `.gitignore` file

### 2. Set up Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub account
3. Select your repository and specify the path: `streamlit_app/app.py`
4. Deploy the app

### 3. Configure Secrets
1. In your Streamlit Cloud app dashboard, go to **Settings** > **Secrets**
2. Add your OANDA API key:
```toml
OANDA_ACCESS_TOKEN = "your-actual-oanda-api-key-here"
```

### 4. App Settings (Optional)
In **Settings** > **General**:
- **Python version**: 3.9+
- **Requirements file**: requirements.txt is automatically detected

## Local Development

### Setup
1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Set up your API key:
   - Option 1: Add to `.streamlit/secrets.toml`:
     ```toml
     OANDA_ACCESS_TOKEN = "your-api-key"
     ```
   - Option 2: Use environment variable:
     ```bash
     export OANDA_ACCESS_TOKEN="your-api-key"
     ```

3. Run the app:
```bash
streamlit run app.py
```

## Configuration

### API Keys
- **Production**: Use Streamlit Cloud secrets management
- **Development**: Use `.streamlit/secrets.toml` or environment variables

### Chart Display
Charts are disabled by default for web deployment. To enable:
```python
# In config.py
SHOW_CHARTS = True
```

### Supported Currency Pairs
- EUR_USD, GBP_USD, USD_JPY, AUD_USD, USD_CAD
- NZD_USD, USD_CHF, EUR_GBP, EUR_JPY, GBP_JPY

## Features Overview

### Single Pair Analysis
- Current signal (BUY/SELL/NO_SIGNAL)
- Confidence level
- Entry price, stop loss, take profit
- Risk-reward ratio
- Trend alignment status

### Multi-Pair Scanner
- Quick overview of all major pairs
- Signal strength indicators
- Best opportunity rankings

### Interactive Charts
- Candlestick price data
- Moving averages
- Volume analysis
- Responsive design

## Security Notes

⚠️ **Important Security Practices:**
1. Never commit API keys to version control
2. Use Streamlit secrets for production deployment
3. Keep your `.streamlit/secrets.toml` file private
4. Regularly rotate your API keys

## Troubleshooting

### Common Issues
1. **API Key Error**: Ensure your OANDA_ACCESS_TOKEN is properly set in secrets
2. **Import Errors**: Check that all required modules are copied to the streamlit_app folder
3. **Chart Issues**: Verify Plotly is installed and working

### Logs
Check Streamlit Cloud logs in your app dashboard for detailed error information.

## Support

For issues related to:
- **Trading Logic**: Check the original strategy modules
- **Streamlit Deployment**: Refer to [Streamlit documentation](https://docs.streamlit.io)
- **OANDA API**: See [OANDA API documentation](https://developer.oanda.com)