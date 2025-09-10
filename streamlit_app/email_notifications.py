import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import streamlit as st
import json
import os

class EmailNotifier:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.port = 587
        self.sent_signals_file = "sent_signals.json"
        self.sent_signals = self.load_sent_signals()  # Load from persistent storage
    
    def load_sent_signals(self):
        """Load sent signals from persistent file storage"""
        try:
            if os.path.exists(self.sent_signals_file):
                with open(self.sent_signals_file, 'r') as f:
                    data = json.load(f)
                    # Clean old signals (older than 24 hours)
                    current_time = datetime.now()
                    cleaned_data = {}
                    
                    for pair, signal_data in data.items():
                        if 'timestamp' in signal_data:
                            signal_time = datetime.fromisoformat(signal_data['timestamp'])
                            # Keep signals from last 24 hours
                            if (current_time - signal_time).total_seconds() < 86400:
                                cleaned_data[pair] = signal_data
                    
                    return cleaned_data
            return {}
        except Exception as e:
            print(f"Error loading sent signals: {e}")
            return {}
    
    def save_sent_signals(self):
        """Save sent signals to persistent file storage"""
        try:
            with open(self.sent_signals_file, 'w') as f:
                json.dump(self.sent_signals, f, indent=2)
        except Exception as e:
            print(f"Error saving sent signals: {e}")

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
            'timestamp': datetime.now().isoformat()
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
            
            # Track this signal with full details and save persistently
            self.sent_signals[pair] = current_signal
            self.save_sent_signals()  # Save to file for persistence across app restarts
            
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