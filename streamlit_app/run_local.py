#!/usr/bin/env python3
"""
Local development runner for Streamlit app
Helps test the app before deployment
"""

import os
import sys
import subprocess

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit', 'pandas', 'numpy', 'plotly', 'oandapyV20'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    return True

def check_config():
    """Check if configuration is set up"""
    secrets_file = ".streamlit/secrets.toml"
    
    if os.path.exists(secrets_file):
        print("✅ Secrets file found")
        with open(secrets_file, 'r') as f:
            content = f.read()
            if "your-oanda-api-key-here" in content:
                print("⚠️  Please update your API key in .streamlit/secrets.toml")
                return False
            else:
                print("✅ API key appears to be configured")
        return True
    else:
        print("❌ No secrets file found")
        print("Please create .streamlit/secrets.toml with your API key")
        return False

def main():
    """Main function to run local tests"""
    print("🚀 Local Streamlit App Testing")
    print("=" * 40)
    
    print("\n📦 Checking Requirements:")
    req_ok = check_requirements()
    
    print("\n🔧 Checking Configuration:")
    config_ok = check_config()
    
    if req_ok and config_ok:
        print("\n✅ All checks passed! Ready to run Streamlit app.")
        print("\nTo start the app:")
        print("  streamlit run app.py")
        print("\nOr run it now? (y/n): ", end="")
        
        try:
            response = input().lower().strip()
            if response in ['y', 'yes']:
                print("\n🎯 Starting Streamlit app...")
                subprocess.run(['streamlit', 'run', 'app.py'])
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
    else:
        print("\n❌ Please fix the issues above before running the app.")

if __name__ == "__main__":
    main()