"""
Enhanced Health Check Server for Render Deployment
Keeps the service alive on free tier with self-ping
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import logging
import time
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Enhanced HTTP handler for health checks"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/' or self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            uptime = getattr(self.server, 'uptime', 'Unknown')
            last_ping = getattr(self.server, 'last_ping', 'Never')
            
            response = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Eva Geises Bot - Always Active</title>
                <meta http-equiv="refresh" content="60">
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        text-align: center;
                        padding: 50px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        margin: 0;
                    }}
                    .container {{
                        background: rgba(255, 255, 255, 0.15);
                        padding: 40px;
                        border-radius: 20px;
                        backdrop-filter: blur(10px);
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                        max-width: 600px;
                        margin: 0 auto;
                    }}
                    h1 {{ 
                        font-size: 3em; 
                        margin: 0 0 20px 0; 
                        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    }}
                    p {{ font-size: 1.2em; margin: 10px 0; }}
                    .status {{
                        background: #10b981;
                        padding: 15px 30px;
                        border-radius: 25px;
                        display: inline-block;
                        margin: 20px 0;
                        font-weight: bold;
                        font-size: 1.3em;
                        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
                        animation: pulse 2s infinite;
                    }}
                    .info {{
                        background: rgba(255, 255, 255, 0.1);
                        padding: 15px;
                        border-radius: 10px;
                        margin: 20px 0;
                        font-size: 0.9em;
                    }}
                    .footer {{
                        margin-top: 30px;
                        font-size: 0.8em;
                        opacity: 0.8;
                    }}
                    @keyframes pulse {{
                        0%, 100% {{ transform: scale(1); }}
                        50% {{ transform: scale(1.05); }}
                    }}
                    .ping {{
                        color: #10b981;
                        font-weight: bold;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🇳🇦 Eva Geises Bot</h1>
                    <div class="status">✅ ACTIVE & RUNNING</div>
                    <p><strong>Namibia Expert & Real Estate Agent</strong></p>
                    <p>🤖 Super Intelligent AI Assistant</p>
                    
                    <div class="info">
                        <p>⏰ <strong>Uptime:</strong> {uptime}</p>
                        <p>🔄 <strong>Last Ping:</strong> <span class="ping">{last_ping}</span></p>
                        <p>📡 <strong>Status:</strong> Online & Monitoring</p>
                        <p>🚀 <strong>Auto-refresh:</strong> Every 60 seconds</p>
                    </div>
                    
                    <p>📱 <strong>Features:</strong></p>
                    <p>✓ 24/7 Group Management</p>
                    <p>✓ Real-time Weather & News</p>
                    <p>✓ AI-Powered Engagement</p>
                    <p>✓ Property Listings</p>
                    
                    <div class="footer">
                        <p>🇳🇦 Serving Namibian Times Community</p>
                        <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            self.wfile.write(response.encode('utf-8'))
        
        elif self.path == '/ping':
            # Simple ping endpoint
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'pong')
        
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        """Suppress standard logs to avoid cluttering"""
        # Only log errors
        if '404' in str(args) or '500' in str(args):
            logger.warning(f"HTTP {args}")

class EnhancedHealthServer:
    """Enhanced health server with self-ping capability"""
    
    def __init__(self, port=10000, service_url=None):
        self.port = port
        self.service_url = service_url or f"https://renderbot-x64y.onrender.com"
        self.server = None
        self.start_time = datetime.now()
        self.last_ping_time = None
        self.ping_thread = None
        self.running = False
    
    def start_server(self):
        """Start the HTTP server"""
        try:
            self.server = HTTPServer(('0.0.0.0', self.port), HealthCheckHandler)
            self.server.uptime = "Starting..."
            self.server.last_ping = "Initializing..."
            self.running = True
            
            logger.info(f"🏥 Enhanced health server running on port {self.port}")
            logger.info(f"🌐 Service URL: {self.service_url}")
            
            # Start self-ping in background
            self.start_self_ping()
            
            # Serve forever
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"❌ Failed to start health server: {e}")
            self.running = False
    
    def start_self_ping(self):
        """Start self-ping to keep service alive"""
        def ping_loop():
            """Ping self every 10 minutes to prevent sleep"""
            logger.info("🔄 Self-ping system started")
            time.sleep(60)  # Wait 1 minute before first ping
            
            while self.running:
                try:
                    # Ping own health endpoint
                    response = requests.get(
                        f"{self.service_url}/health",
                        timeout=10
                    )
                    
                    self.last_ping_time = datetime.now()
                    uptime = datetime.now() - self.start_time
                    
                    # Update server attributes
                    if self.server:
                        hours = int(uptime.total_seconds() // 3600)
                        minutes = int((uptime.total_seconds() % 3600) // 60)
                        self.server.uptime = f"{hours}h {minutes}m"
                        self.server.last_ping = self.last_ping_time.strftime('%H:%M:%S')
                    
                    if response.status_code == 200:
                        logger.info(f"✅ Self-ping successful - Uptime: {hours}h {minutes}m")
                    else:
                        logger.warning(f"⚠️ Self-ping returned {response.status_code}")
                
                except Exception as e:
                    logger.error(f"❌ Self-ping failed: {e}")
                
                # Ping every 10 minutes (600 seconds)
                # This keeps Render service awake
                time.sleep(600)
        
        self.ping_thread = threading.Thread(
            target=ping_loop,
            daemon=True,
            name="SelfPingThread"
        )
        self.ping_thread.start()
        logger.info("🔄 Self-ping thread started (pings every 10 minutes)")
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.server:
            self.server.shutdown()

def start_health_server(port=10000, service_url=None):
    """Start the enhanced health check server"""
    server = EnhancedHealthServer(port, service_url)
    server.start_server()

def run_health_server_background(port=10000, service_url=None):
    """Run enhanced health server in background thread"""
    health_thread = threading.Thread(
        target=start_health_server,
        args=(port, service_url),
        daemon=True,
        name="EnhancedHealthServer"
    )
    health_thread.start()
    logger.info("✅ Enhanced health server started in background")
    logger.info("🔄 Self-ping enabled - Service will stay awake!")
