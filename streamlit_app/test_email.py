#!/usr/bin/env python3
"""
Test script for email notifications
Run this to test your email configuration before using the main app
"""

import os
import sys
from email_notifications import EmailNotifier

def test_email_notifications():
    """Test email notification functionality"""
    
    print("🧪 Testing Email Notification System")
    print("=" * 50)
    
    # Create notifier
    notifier = EmailNotifier()
    
    # Test configuration
    print("1. Testing email configuration...")
    success, message = notifier.test_email_connection()
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
        print("\n📋 Setup Instructions:")
        print("To use email notifications, set these environment variables or Streamlit secrets:")
        print("- SENDER_EMAIL: Your Gmail address")
        print("- SENDER_PASSWORD: Your Gmail app password (not regular password)")
        print("- RECIPIENT_EMAIL: Where to send alerts")
        print("\n⚠️ For Gmail, you need to:")
        print("1. Enable 2-factor authentication")
        print("2. Generate an App Password (not your regular password)")
        print("3. Use the App Password in SENDER_PASSWORD")
        return False
    
    # Test sending a sample notification
    print("\n2. Testing sample notification...")
    success, message = notifier.send_signal_notification(
        pair="TEST_PAIR",
        signal="BULLISH_SIGNAL",
        confidence=75,
        entry_price=1.2345,
        take_profit=1.2400,
        stop_loss=1.2290
    )
    
    if success:
        print(f"✅ {message}")
        print("📧 Check your email inbox for the test notification!")
    else:
        print(f"❌ {message}")
        return False
    
    print("\n🎉 All tests passed! Email notifications are ready to use.")
    return True

if __name__ == "__main__":
    # Set up environment variables if needed
    print("Email Notification Test")
    print("Make sure you have set the following:")
    print("- SENDER_EMAIL")
    print("- SENDER_PASSWORD") 
    print("- RECIPIENT_EMAIL")
    print()
    
    test_email_notifications()