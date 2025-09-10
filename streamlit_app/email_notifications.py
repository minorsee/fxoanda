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
    
    def get_google_sheets_client(self):
        """Initialize Google Sheets client using service account credentials"""
        try:
            # Get service account credentials from Streamlit secrets
            service_account_info = st.secrets["gcp_service_account"]
            
            # Define the scope
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Create credentials
            credentials = Credentials.from_service_account_info(
                service_account_info, scopes=scopes
            )
            
            # Initialize the client
            client = gspread.authorize(credentials)
            return client
            
        except Exception as e:
            if hasattr(st, 'session_state') and 'email_logs' not in st.session_state:
                st.session_state.email_logs = []
            if hasattr(st, 'session_state'):
                st.session_state.email_logs.append(f"❌ Google Sheets error: {str(e)[:50]}...")
            return None
    
    def load_sent_signals_from_sheets(self):
        """Load sent signals from Google Sheets"""
        try:
            client = self.get_google_sheets_client()
            if not client:
                return
            
            # Try to open existing sheet or create new one
            try:
                sheet = client.open(self.sheet_name).sheet1
            except gspread.SpreadsheetNotFound:
                # Create new spreadsheet
                spreadsheet = client.create(self.sheet_name)
                sheet = spreadsheet.sheet1
                
                # Set up headers
                headers = [['Pair', 'Signal', 'Entry Price', 'Take Profit', 'Stop Loss', 'Date', 'Time', 'Confidence']]
                sheet.update('A1:H1', headers)
                
                # Log sheet creation
                if hasattr(st, 'session_state'):
                    if 'email_logs' not in st.session_state:
                        st.session_state.email_logs = []
                    st.session_state.email_logs.append(f"✅ Created sheet: {spreadsheet.url[:50]}...")
            
            # Load all records
            records = sheet.get_all_records()
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
                except:
                    continue
                    
        except Exception as e:
            if hasattr(st, 'session_state'):
                if 'email_logs' not in st.session_state:
                    st.session_state.email_logs = []
                st.session_state.email_logs.append(f"❌ Load error: {str(e)[:50]}...")
    
    def save_signal_to_sheets(self, pair, signal_data):
        """Save new signal to Google Sheets"""
        try:
            client = self.get_google_sheets_client()
            if not client:
                return False
                
            sheet = client.open(self.sheet_name).sheet1
            
            # Prepare row data with separate date and time columns
            now = datetime.now()
            row = [
                pair,
                signal_data['signal'],
                signal_data['entry_price'] or '',
                signal_data['take_profit'] or '',
                signal_data['stop_loss'] or '',
                now.date().isoformat(),  # Date column (YYYY-MM-DD)
                now.time().strftime('%H:%M:%S'),  # Time column (HH:MM:SS)
                signal_data.get('confidence', '')
            ]
            
            # Add to sheet
            sheet.append_row(row)
            
            # Log success
            if hasattr(st, 'session_state'):
                if 'email_logs' not in st.session_state:
                    st.session_state.email_logs = []
                direction = "BULLISH" if "BULLISH" in signal_data['signal'] else "BEARISH"
                st.session_state.email_logs.append(f"📧 Sent: {direction} {pair} @ {signal_data['entry_price']}")
            
            return True
            
        except Exception as e:
            if hasattr(st, 'session_state'):
                if 'email_logs' not in st.session_state:
                    st.session_state.email_logs = []
                st.session_state.email_logs.append(f"❌ Save error: {str(e)[:50]}...")
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
        
        # Simple check: Does this exact signal exist in Google Sheets today?
        current_direction = "BULLISH" if "BULLISH" in signal else "BEARISH" 
        current_date = datetime.now().date().isoformat()
        current_entry = round(entry_price, 5) if entry_price else None
        current_tp = round(take_profit, 5) if take_profit else None
        current_sl = round(stop_loss, 5) if stop_loss else None
        
        try:
            client = self.get_google_sheets_client()
            if not client:
                return False, "Cannot connect to Google Sheets"
                
            # Create sheet if doesn't exist
            try:
                sheet = client.open(self.sheet_name).sheet1
            except gspread.SpreadsheetNotFound:
                spreadsheet = client.create(self.sheet_name)
                sheet = spreadsheet.sheet1
                headers = [['Pair', 'Signal', 'Entry Price', 'Take Profit', 'Stop Loss', 'Date', 'Time', 'Confidence']]
                sheet.update('A1:H1', headers)
            
            # Check if exact match exists in sheet (only check: pair, entry, tp, sl, date)
            records = sheet.get_all_records()
            
            # DEBUG: Show what we're looking for
            st.write(f"🔍 **CHECKING:** {pair} @ {current_entry} | TP:{current_tp} | SL:{current_sl} | Date:{current_date}")
            st.write(f"📋 **FOUND {len(records)} records in sheet**")
            
            for i, record in enumerate(records):
                try:
                    # Get values from sheet
                    sheet_pair = record.get('Pair', '')
                    sheet_date = record.get('Date', '')
                    sheet_entry = round(float(record.get('Entry Price', 0)), 5) if record.get('Entry Price') else None
                    sheet_tp = round(float(record.get('Take Profit', 0)), 5) if record.get('Take Profit') else None  
                    sheet_sl = round(float(record.get('Stop Loss', 0)), 5) if record.get('Stop Loss') else None
                    
                    # DEBUG: Show each comparison
                    st.write(f"Row {i+1}: {sheet_pair} @ {sheet_entry} | TP:{sheet_tp} | SL:{sheet_sl} | Date:{sheet_date}")
                    
                    # Check if ALL 5 criteria match: pair + entry + tp + sl + date
                    if (sheet_pair == pair and
                        sheet_entry == current_entry and
                        sheet_tp == current_tp and
                        sheet_sl == current_sl and
                        sheet_date == current_date):
                        
                        st.write(f"🚫 **MATCH FOUND - BLOCKING EMAIL**")
                        return False, f"Duplicate: {pair} @ {current_entry} already sent {current_date}"
                        
                except (ValueError, TypeError):
                    st.write(f"Row {i+1}: Invalid data - skipping")
                    continue  # Skip invalid rows
            
            st.write(f"✅ **NO MATCH FOUND - SENDING EMAIL**")
            
            # No match found - send email and save to sheet
            
        except Exception as e:
            return False, f"Sheet error: {str(e)}"
        
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
            
            # Save this signal to Google Sheets
            now = datetime.now()
            row = [
                pair,
                signal,
                current_entry or '',
                current_tp or '',
                current_sl or '',
                current_date,
                now.time().strftime('%H:%M:%S'),
                confidence
            ]
            sheet.append_row(row)
            
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