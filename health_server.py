"""
Health Check Server for Render Deployment
Add this to keep the service alive on free tier
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import logging

logger = logging.getLogger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/' or self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            response = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Eva Geises Bot</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        text-align: center;
                        padding: 50px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                    }
                    .container {
                        background: rgba(255, 255, 255, 0.1);
                        padding: 30px;
                        border-radius: 10px;
                        backdrop-filter: blur(10px);
                    }
                    h1 { font-size: 3em; margin: 0; }
                    p { font-size: 1.2em; }
                    .status {
                        background: #10b981;
                        padding: 10px 20px;
                        border-radius: 20px;
                        display: inline-block;
                        margin: 20px 0;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🇳🇦 Eva Geises Bot</h1>
                    <div class="status">✅ Bot is Running</div>
                    <p>Namibia Expert & Real Estate Agent</p>
                    <p>Find me on Telegram!</p>
                </div>
            </body>
            </html>
            """
            
            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress standard logs to avoid cluttering"""
        pass

def start_health_server(port=10000):
    """Start the health check server in a separate thread"""
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"🏥 Health check server running on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Failed to start health server: {e}")

def run_health_server_background(port=10000):
    """Run health server in background thread"""
    health_thread = threading.Thread(
        target=start_health_server,
        args=(port,),
        daemon=True,
        name="HealthCheckServer"
    )
    health_thread.start()
    logger.info("✅ Health check server started in background")
