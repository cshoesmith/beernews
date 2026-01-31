#!/usr/bin/env python3
"""
Sydney Beer Aggregator - Startup Script

This app helps you discover new beer releases at Sydney's best breweries and bars.
It aggregates social media feeds and recommends venues based on your location and preferences.
"""
import webbrowser
import threading
import time
from main import app

def open_browser():
    """Open browser after a short delay to ensure server is running."""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    print("=" * 60)
    print("Sydney Beer Aggregator")
    print("=" * 60)
    print("\nStarting server at http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    # Open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start Flask server
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
