import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

class EmailNotifier:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.port = 587
        self.sheet_name = "Trading Signal History"
        self.sent_signals = {}  # Will be loaded from Google Sheets
        self.load_sent_signals_from_sheets()
    
    def get_google_sheets_client(self):
        """Initialize Google Sheets client using service account credentials"""
        try:
            st.write("🔧 **DEBUG:** Attempting to initialize Google Sheets client...")
            
            # Get service account credentials from Streamlit secrets
            service_account_info = st.secrets["gcp_service_account"]
            st.write(f"✅ **DEBUG:** Service account credentials found: {service_account_info.get('client_email', 'No email found')}")
            
            # Define the scope
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Create credentials
            credentials = Credentials.from_service_account_info(
                service_account_info, scopes=scopes
            )
            st.write("✅ **DEBUG:** Credentials created successfully")
            
            # Initialize the client
            client = gspread.authorize(credentials)
            st.write("✅ **DEBUG:** Google Sheets client authorized successfully")
            return client
            
        except Exception as e:
            st.error(f"❌ **DEBUG:** Error initializing Google Sheets client: {e}")
            return None
    
    def load_sent_signals_from_sheets(self):
        """Load sent signals from Google Sheets"""
        try:
            st.write("🔧 **DEBUG:** Loading sent signals from Google Sheets...")
            client = self.get_google_sheets_client()
            if not client:
                st.error("❌ **DEBUG:** No Google Sheets client - cannot load signals")
                return
            
            # Try to open existing sheet or create new one
            try:
                st.write(f"🔧 **DEBUG:** Looking for existing sheet: '{self.sheet_name}'")
                sheet = client.open(self.sheet_name).sheet1
                st.write("✅ **DEBUG:** Found existing sheet!")
            except gspread.SpreadsheetNotFound:
                st.write("🔧 **DEBUG:** Sheet not found, creating new one...")
                # Create new spreadsheet
                spreadsheet = client.create(self.sheet_name)
                sheet = spreadsheet.sheet1
                st.write(f"✅ **DEBUG:** Created new sheet: {spreadsheet.url}")
                
                # Set up headers
                headers = [['Pair', 'Signal', 'Entry Price', 'Take Profit', 'Stop Loss', 'Timestamp', 'Confidence']]
                sheet.update('A1:G1', headers)
                st.write("✅ **DEBUG:** Headers added to sheet")
            
            # Load all records
            records = sheet.get_all_records()
            st.write(f"🔧 **DEBUG:** Loaded {len(records)} records from sheet")
            current_time = datetime.now()
            
            for record in records:
                if not record.get('Pair'):  # Skip empty rows
                    continue
                    
                pair = record['Pair']
                timestamp_str = record.get('Timestamp', '')
                
                # Only keep signals from last 24 hours
                try:
                    if timestamp_str:
                        signal_time = datetime.fromisoformat(timestamp_str)
                        if (current_time - signal_time).total_seconds() < 86400:
                            self.sent_signals[pair] = {
                                'signal': record.get('Signal', ''),
                                'entry_price': float(record.get('Entry Price', 0)) if record.get('Entry Price') else None,
                                'take_profit': float(record.get('Take Profit', 0)) if record.get('Take Profit') else None,
                                'stop_loss': float(record.get('Stop Loss', 0)) if record.get('Stop Loss') else None,
                                'timestamp': timestamp_str
                            }
                except Exception as e:
                    st.error(f"❌ **DEBUG:** Error parsing record for {pair}: {e}")
                    continue
            
            st.write(f"✅ **DEBUG:** Loaded {len(self.sent_signals)} valid signals from last 24h")
                    
        except Exception as e:
            st.error(f"❌ **DEBUG:** Error loading sent signals from Google Sheets: {e}")
    
    def save_signal_to_sheets(self, pair, signal_data):
        """Save new signal to Google Sheets"""
        try:
            st.write(f"🔧 **DEBUG:** Saving signal for {pair} to Google Sheets...")
            client = self.get_google_sheets_client()
            if not client:
                st.error("❌ **DEBUG:** No Google Sheets client - cannot save signal")
                return False
                
            sheet = client.open(self.sheet_name).sheet1
            
            # Prepare row data
            row = [
                pair,
                signal_data['signal'],
                signal_data['entry_price'] or '',
                signal_data['take_profit'] or '',
                signal_data['stop_loss'] or '',
                signal_data['timestamp'],
                signal_data.get('confidence', '')
            ]
            
            st.write(f"🔧 **DEBUG:** Row data: {row}")
            
            # Add to sheet
            sheet.append_row(row)
            st.write(f"✅ **DEBUG:** Signal saved to sheet successfully!")
            return True
            
        except Exception as e:
            st.error(f"❌ **DEBUG:** Error saving signal to Google Sheets: {e}")
            return False

    def get_email_config(self):
        """Get email configuration from Streamlit secrets"""
        try:
            sender_email = st.secrets.get("SENDER_EMAIL", "")
            sender_password = st.secrets.get("SENDER_PASSWORD", "")
            recipient_email = st.secrets.get("RECIPIENT_EMAIL", "")
            
            if not all([sender_email, sender_password, recipient_email]):
                return None, None, None
                
            return sender_email, sender_password, recipient_email
        except:
            return None, None, None
    
    def send_signal_notification(self, pair, signal, confidence, entry_price, take_profit=None, stop_loss=None):
        """Send email notification for high confidence trading signal"""
        
        # Create signal state dictionary for comparison with timestamp
        current_signal = {
            'pair': pair,
            'signal': signal,
            'entry_price': round(entry_price, 5) if entry_price else None,
            'take_profit': round(take_profit, 5) if take_profit else None,
            'stop_loss': round(stop_loss, 5) if stop_loss else None,
            'timestamp': datetime.now().isoformat(),
            'confidence': confidence
        }
        
        # Check if this exact signal was already sent
        if pair in self.sent_signals:
            last_signal = self.sent_signals[pair]
            if (last_signal['signal'] == current_signal['signal'] and 
                last_signal['entry_price'] == current_signal['entry_price'] and
                last_signal['take_profit'] == current_signal['take_profit'] and
                last_signal['stop_loss'] == current_signal['stop_loss']):
                return False, "Identical signal already sent - no duplicate email"
        
        sender_email, sender_password, recipient_email = self.get_email_config()
        
        if not all([sender_email, sender_password, recipient_email]):
            return False, "Email configuration not found in secrets"
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"🚨 Trading Alert: {pair} - {confidence}% Confidence"
            message["From"] = sender_email
            message["To"] = recipient_email
            
            # Create the HTML content
            direction = "BUY 🚀" if "BULLISH" in signal else "SELL 🔻"
            color = "#26a69a" if "BULLISH" in signal else "#ef5350"
            
            html = f"""
            <html>
              <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                  <div style="background-color: {color}; color: white; padding: 20px; text-align: center;">
                    <h1>🚨 Trading Signal Alert</h1>
                    <h2>{pair} - {confidence}% Confidence</h2>
                  </div>
                  
                  <div style="padding: 20px; background-color: #f9f9f9;">
                    <h3 style="color: {color};">Signal: {direction}</h3>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                      <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #fff;"><strong>Currency Pair:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #fff;">{pair}</td>
                      </tr>
                      <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #fff;"><strong>Signal:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #fff;">{direction}</td>
                      </tr>
                      <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #fff;"><strong>Confidence:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #fff;">{confidence}%</td>
                      </tr>
                      <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #fff;"><strong>Entry Price:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #fff;">{entry_price:.5f}</td>
                      </tr>
            """
            
            if take_profit:
                html += f"""
                      <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #fff;"><strong>Take Profit:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #fff;">{take_profit:.5f}</td>
                      </tr>
                """
            
            if stop_loss:
                html += f"""
                      <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #fff;"><strong>Stop Loss:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #fff;">{stop_loss:.5f}</td>
                      </tr>
                """
            
            html += f"""
                    </table>
                    
                    <div style="margin: 20px 0; padding: 15px; background-color: #e8f5e8; border-left: 4px solid #26a69a;">
                      <strong>⚠️ Trading Alert:</strong> This signal has exceeded your 60% confidence threshold.
                      Please review the signal and make your trading decision accordingly.
                    </div>
                    
                    <p style="color: #666; font-size: 12px; margin-top: 30px;">
                      Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                      This is an automated notification from your Trading Dashboard.
                    </p>
                  </div>
                </div>
              </body>
            </html>
            """
            
            # Convert to MIMEText object
            part = MIMEText(html, "html")
            message.attach(part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.starttls(context=context)
                server.login(sender_email, sender_password)
                text = message.as_string()
                server.sendmail(sender_email, recipient_email, text)
            
            # Track this signal and save to Google Sheets
            self.sent_signals[pair] = current_signal
            self.save_signal_to_sheets(pair, current_signal)
            
            # Also save to streamlit session state for UI display
            if 'sent_signals' in st.session_state:
                st.session_state.sent_signals = self.sent_signals
            
            return True, "Email notification sent successfully"
            
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    def test_email_connection(self):
        """Test email configuration"""
        sender_email, sender_password, recipient_email = self.get_email_config()
        
        if not all([sender_email, sender_password, recipient_email]):
            return False, "Email configuration missing"
        
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.starttls(context=context)
                server.login(sender_email, sender_password)
            return True, "Email configuration is valid"
        except Exception as e:
            return False, f"Email configuration error: {str(e)}"