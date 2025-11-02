"""
External Bot Pinger for PythonAnywhere
Keeps your Render Telegram bot alive 24/7

Setup Instructions:
1. Go to pythonanywhere.com and create free account
2. Upload this file to Files tab
3. Change BOT_URL below to your Render URL
4. Test: python3 bot_pinger.py
5. Create scheduled task: */8 * * * * (every 8 minutes)
"""
import requests
import sys
from datetime import datetime

# ⚠️ CONFIGURE THIS - Your Render bot URL
BOT_URL = "https://recoveredbot.onrender.com"

def log(message):
    """Print with timestamp (PythonAnywhere-friendly)"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()  # Important for PythonAnywhere logging

def ping_bot():
    """Ping the bot to keep it alive"""
    endpoints = [
        f"{BOT_URL}/health",
        f"{BOT_URL}/",
    ]
    
    for endpoint in endpoints:
        try:
            log(f"🏓 Pinging {endpoint}")
            response = requests.get(endpoint, timeout=15)
            
            if response.status_code == 200:
                log(f"✅ SUCCESS - Status: {response.status_code}")
                return True
            else:
                log(f"⚠️ Returned status {response.status_code}")
                
        except requests.exceptions.Timeout:
            log(f"❌ TIMEOUT - {endpoint}")
            
        except requests.exceptions.ConnectionError:
            log(f"❌ CONNECTION ERROR - {endpoint}")
            
        except Exception as e:
            log(f"❌ ERROR - {str(e)[:50]}")
    
    return False

def main():
    """Main function - runs on each scheduled execution"""
    log("=" * 60)
    log("🚀 PythonAnywhere Bot Pinger")
    log(f"🎯 Target: {BOT_URL}")
    
    # Validate configuration
    if "YOUR-SERVICE-NAME" in BOT_URL:
        log("❌ ERROR: BOT_URL not configured!")
        log("📝 Edit this file and set BOT_URL to your Render URL")
        log("   Example: https://trading-bot-xyz.onrender.com")
        sys.exit(1)
    
    # Ping the bot
    success = ping_bot()
    
    if success:
        log("✅ Ping completed successfully")
        log("🎉 Your bot is alive and responding!")
    else:
        log("❌ All ping attempts failed!")
        log("🚨 Check your Render service status!")
    
    log("⏰ Next ping in 8 minutes...")
    log("=" * 60)

if __name__ == "__main__":
    main()