"""
Simple health check server for Render
Create this file as health_server.py in your project root
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import os
import logging

logger = logging.getLogger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write('Trading Bot is running! ✅'.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress HTTP access logs"""
        pass

def start_health_server():
    """Start health check server on PORT"""
    port = int(os.environ.get('PORT', 10000))
    
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"✅ Health check server running on port {port}")
        
        # Run in background thread
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        
        return server
    except Exception as e:
        logger.error(f"Failed to start health server: {e}")
        return None