import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import streamlit as st

class EmailNotifier:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.port = 587
        self.sent_notifications = set()  # Track sent notifications to avoid spam
    
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
        
        # Create unique key for this signal to avoid duplicate notifications
        signal_key = f"{pair}_{signal}_{confidence}_{datetime.now().strftime('%Y%m%d%H')}"
        
        if signal_key in self.sent_notifications:
            return False, "Notification already sent for this signal"
        
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
            
            # Track this notification
            self.sent_notifications.add(signal_key)
            
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