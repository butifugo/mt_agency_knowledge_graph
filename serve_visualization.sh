#!/bin/bash
# Simple HTTP server to view the agency navigation visualization
# This is needed because browsers block fetch() requests on file:// protocol

echo "Starting local web server..."
echo "============================================"
echo "Open in browser: http://localhost:8000/agency-navigation.html"
echo "Press Ctrl+C to stop the server"
echo "============================================"
echo ""

cd html && python3 -m http.server 8000
