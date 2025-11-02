"""
Keep Render service alive by self-pinging every 14 minutes
This prevents the free tier from spinning down after 15 minutes of inactivity
"""
import requests
import logging
import os
from threading import Thread
import time

logger = logging.getLogger(__name__)

def keep_alive():
    """Ping the service every 14 minutes to prevent spin-down"""
    
    # Get your Render service URL from environment
    service_url = os.environ.get('RENDER_EXTERNAL_URL', '').rstrip('/')
    
    if not service_url:
        logger.warning("⚠️ RENDER_EXTERNAL_URL not set - keep_alive disabled")
        logger.warning("Set it in Render Dashboard → Environment: RENDER_EXTERNAL_URL=https://your-service.onrender.com")
        return
    
    ping_url = f"{service_url}/health"
    ping_interval = 840  # 14 minutes in seconds (840 = 14 * 60)
    
    logger.info(f"🔄 Keep-alive started - will ping {ping_url} every {ping_interval // 60} minutes")
    
    # Wait a bit before first ping to let server fully start
    time.sleep(60)
    
    ping_count = 0
    
    while True:
        try:
            ping_count += 1
            logger.info(f"🏓 Sending keep-alive ping #{ping_count} to {ping_url}")
            
            response = requests.get(ping_url, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ Keep-alive ping #{ping_count} successful (status: {response.status_code})")
            else:
                logger.warning(f"⚠️ Keep-alive ping #{ping_count} returned status {response.status_code}")
        
        except requests.exceptions.Timeout:
            logger.error(f"❌ Keep-alive ping #{ping_count} timed out")
        
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Keep-alive ping #{ping_count} connection error: {e}")
        
        except Exception as e:
            logger.error(f"❌ Keep-alive ping #{ping_count} failed: {e}")
        
        # Wait before next ping
        logger.info(f"⏰ Next ping in {ping_interval // 60} minutes...")
        time.sleep(ping_interval)

def start_keep_alive():
    """Start keep-alive in background thread"""
    try:
        thread = Thread(target=keep_alive, daemon=True, name="KeepAlive")
        thread.start()
        logger.info("🚀 Keep-alive thread started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start keep-alive thread: {e}")

if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)
    start_keep_alive()
    
    # Keep main thread alive for testing
    while True:
        time.sleep(60)