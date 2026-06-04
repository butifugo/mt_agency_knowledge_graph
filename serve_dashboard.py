#!/usr/bin/env python3
"""
Simple HTTP server for the interactive dashboard
Serves files from the html directory on localhost
"""

import http.server
import socketserver
import os
from pathlib import Path

# Change to html directory
html_dir = Path(__file__).parent / "html"
os.chdir(html_dir)

PORT = 8000

Handler = http.server.SimpleHTTPRequestHandler

# Add CORS headers to allow local development
class CORSRequestHandler(Handler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
    print(f"✓ Server started at http://localhost:{PORT}")
    print(f"✓ Serving files from: {html_dir}")
    print(f"\n📊 Open dashboard at: http://localhost:{PORT}/interactive-dashboard.html")
    print("\n Press Ctrl+C to stop the server\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
