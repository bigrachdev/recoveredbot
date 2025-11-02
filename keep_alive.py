"""
Aggressive Keep Render service alive - Multiple strategies
Pings every 10 minutes + uses multiple endpoints
"""
import requests
import logging
import os
from threading import Thread
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class KeepAliveManager:
    def __init__(self):
        self.service_url = os.environ.get('RENDER_EXTERNAL_URL', '').rstrip('/')
        self.ping_interval = 600  # 10 minutes (well before 15 min timeout)
        self.ping_count = 0
        self.failed_pings = 0
        self.last_successful_ping = None
        
    def ping_health_endpoint(self):
        """Ping the health endpoint"""
        if not self.service_url:
            logger.warning("⚠️ RENDER_EXTERNAL_URL not set - keep_alive disabled")
            return False
        
        ping_url = f"{self.service_url}/health"
        
        try:
            self.ping_count += 1
            logger.info(f"🏓 Keep-alive ping #{self.ping_count} to {ping_url}")
            
            response = requests.get(ping_url, timeout=15)
            
            if response.status_code == 200:
                self.failed_pings = 0
                self.last_successful_ping = datetime.now()
                logger.info(f"✅ Ping #{self.ping_count} SUCCESS (status: {response.status_code}, time: {datetime.now().strftime('%H:%M:%S')})")
                return True
            else:
                self.failed_pings += 1
                logger.warning(f"⚠️ Ping #{self.ping_count} returned {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            self.failed_pings += 1
            logger.error(f"❌ Ping #{self.ping_count} TIMEOUT (>15s)")
            return False
            
        except requests.exceptions.ConnectionError as e:
            self.failed_pings += 1
            logger.error(f"❌ Ping #{self.ping_count} CONNECTION ERROR: {e}")
            return False
            
        except Exception as e:
            self.failed_pings += 1
            logger.error(f"❌ Ping #{self.ping_count} FAILED: {e}")
            return False
    
    def keep_alive_loop(self):
        """Main keep-alive loop with aggressive pinging"""
        
        if not self.service_url:
            logger.error("❌ RENDER_EXTERNAL_URL not set!")
            logger.error("Set it in Render: RENDER_EXTERNAL_URL=https://your-service.onrender.com")
            return
        
        logger.info(f"🔄 Aggressive keep-alive started")
        logger.info(f"📍 Target: {self.service_url}")
        logger.info(f"⏰ Interval: {self.ping_interval // 60} minutes ({self.ping_interval}s)")
        logger.info(f"🎯 Strategy: Ping before 15-min Render timeout")
        
        # Wait 30 seconds for server to fully start
        logger.info("⏳ Waiting 30s for server initialization...")
        time.sleep(30)
        
        # First immediate ping
        logger.info("🚀 Sending first ping immediately...")
        self.ping_health_endpoint()
        
        # Main loop - ping every 10 minutes
        while True:
            try:
                # Calculate next ping time
                next_ping_time = datetime.now().timestamp() + self.ping_interval
                next_ping_str = datetime.fromtimestamp(next_ping_time).strftime('%H:%M:%S')
                
                logger.info(f"⏰ Next ping at {next_ping_str} (in {self.ping_interval // 60} minutes)")
                
                # Sleep until next ping
                time.sleep(self.ping_interval)
                
                # Send ping
                success = self.ping_health_endpoint()
                
                # Alert if multiple failures
                if self.failed_pings >= 3:
                    logger.error(f"🚨 ALERT: {self.failed_pings} consecutive ping failures!")
                    logger.error(f"🚨 Bot may be spinning down! Check Render dashboard!")
                
                # Show status every 5 pings
                if self.ping_count % 5 == 0:
                    uptime_hours = (self.ping_count * self.ping_interval) // 3600
                    logger.info(f"📊 Stats: {self.ping_count} pings, ~{uptime_hours}h uptime, {self.failed_pings} failures")
                
            except Exception as e:
                logger.error(f"💥 Keep-alive loop error: {e}")
                time.sleep(60)  # Wait 1 minute before retry

def start_keep_alive():
    """Start aggressive keep-alive in background thread"""
    try:
        manager = KeepAliveManager()
        thread = Thread(target=manager.keep_alive_loop, daemon=True, name="AggressiveKeepAlive")
        thread.start()
        logger.info("🚀 Aggressive keep-alive thread started")
        return manager
    except Exception as e:
        logger.error(f"❌ Failed to start keep-alive: {e}")
        return None

# Test function
def test_keep_alive():
    """Test the keep-alive functionality"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("🧪 Testing keep-alive system...")
    
    # Check if URL is set
    url = os.environ.get('RENDER_EXTERNAL_URL')
    if not url:
        logger.error("❌ RENDER_EXTERNAL_URL not set!")
        logger.error("Run: export RENDER_EXTERNAL_URL=https://your-service.onrender.com")
        return
    
    logger.info(f"✅ URL configured: {url}")
    
    # Test single ping
    manager = KeepAliveManager()
    success = manager.ping_health_endpoint()
    
    if success:
        logger.info("✅ Test ping successful!")
        logger.info("🚀 Starting continuous keep-alive...")
        manager.keep_alive_loop()
    else:
        logger.error("❌ Test ping failed!")
        logger.error("Check if your service is running and /health endpoint works")

if __name__ == "__main__":
    test_keep_alive()