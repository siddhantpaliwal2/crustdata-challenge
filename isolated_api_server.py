#!/usr/bin/env python
"""
Isolated REST API server for Browser-AI that runs the browser in a separate process

This version uses multiprocessing to completely isolate the browser from the Flask server,
solving the thread conflicts that can occur with Playwright.

Usage:
    python isolated_api_server.py [--port PORT] [--host HOST] [--debug]

Example curl command:
    curl -X POST http://localhost:5020/execute -H "Content-Type: application/json" -d '{"command": "Navigate to google.com"}'
"""

import os
import sys
import json
import argparse
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the browser process manager
from browser_ai.browser_process import BrowserProcessManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global browser manager
browser_manager = BrowserProcessManager()
browser_config = {
    "headless": False,
    "browser_type": "chromium"
}


@app.route('/status', methods=['GET'])
def status():
    """Get the current status of the browser session"""
    logger.info("Received request to /status endpoint")
    
    # Get status from browser manager
    status_result = browser_manager.get_status()
    return jsonify(status_result)


@app.route('/start', methods=['POST'])
def start_browser():
    """Start a new browser session"""
    global browser_config
    logger.info("Received request to /start endpoint")
    
    # Parse request data
    data = request.json or {}
    browser_config["headless"] = data.get('headless', False)
    browser_config["browser_type"] = data.get('browser_type', 'chromium')
    logger.info(f"Start parameters: headless={browser_config['headless']}, browser_type={browser_config['browser_type']}")
    
    # Start browser process
    success, error = browser_manager.start(
        headless=browser_config["headless"],
        browser_type=browser_config["browser_type"]
    )
    
    if success:
        return jsonify({
            "status": "success",
            "message": f"Browser session started ({browser_config['browser_type']}, headless={browser_config['headless']})"
        })
    else:
        return jsonify({
            "status": "error",
            "message": error or "Failed to start browser session"
        })


@app.route('/stop', methods=['POST'])
def stop_browser():
    """Stop the current browser session"""
    logger.info("Received request to /stop endpoint")
    
    # Stop browser process
    success, error = browser_manager.stop()
    
    if success:
        return jsonify({
            "status": "success",
            "message": "Browser session ended"
        })
    else:
        return jsonify({
            "status": "warning",
            "message": f"Browser session closed with warnings: {error}"
        })


@app.route('/execute', methods=['POST'])
def execute_command():
    """Execute a natural language command"""
    logger.info("Received request to /execute endpoint")
    
    # Get command from request
    data = request.json
    if not data or 'command' not in data:
        return jsonify({
            "status": "error",
            "message": "Missing 'command' in request body"
        })
    
    command = data['command']
    logger.info(f"Executing command: {command}")
    
    # Make sure browser is active
    status_result = browser_manager.get_status()
    if status_result.get("status") != "active":
        # Try to start the browser if it's not active
        success, error = browser_manager.start(
            headless=browser_config["headless"],
            browser_type=browser_config["browser_type"]
        )
        
        if not success:
            return jsonify({
                "status": "error",
                "message": f"Browser is not active and could not be started: {error}",
                "command": command
            })
    
    # Execute the command
    result = browser_manager.execute(command)
    
    return jsonify({
        "status": "success" if result.get('success', False) else "error",
        "result": result
    })


@app.route('/screenshot', methods=['POST'])
def take_screenshot():
    """Take a screenshot and return the file path"""
    logger.info("Received request to /screenshot endpoint")
    
    # Get filename from request
    data = request.json or {}
    filename = data.get('filename', 'screenshot.png')
    
    # Take screenshot
    result = browser_manager.take_screenshot(filename)
    
    return jsonify({
        "status": "success" if result.get('success', False) else "error",
        "filename": filename,
        "result": result
    })


@app.route('/dom', methods=['GET'])
def get_dom():
    """Get the current DOM snapshot"""
    logger.info("Received request to /dom endpoint")
    
    # Get DOM snapshot
    result = browser_manager.get_dom_snapshot()
    
    if 'dom_snapshot' in result:
        return jsonify({
            "status": "success",
            "dom_snapshot": result['dom_snapshot']
        })
    else:
        return jsonify({
            "status": "error",
            "message": result.get('error', 'Unknown error getting DOM snapshot')
        })


@app.route('/inspect', methods=['POST'])
def inspect_element():
    """Inspect a specific element on the page"""
    logger.info("Received request to /inspect endpoint")
    
    # Get selector from request
    data = request.json
    if not data or 'selector' not in data:
        return jsonify({
            "status": "error",
            "message": "Missing 'selector' in request body"
        })
    
    selector = data['selector']
    
    # Inspect element
    result = browser_manager.inspect_element(selector)
    
    if 'element' in result:
        return jsonify({
            "status": "success",
            "element": result['element']
        })
    else:
        return jsonify({
            "status": "error",
            "message": result.get('error', 'Unknown error inspecting element')
        })


def main():
    """Main function to start the API server"""
    parser = argparse.ArgumentParser(description='Browser-AI Isolated REST API Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=5020, help='Port to bind the server to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not found in environment variables or .env file.")
        print("Please set your OpenAI API key before making API calls.")
    
    print(f"Starting Browser-AI Isolated API server at http://{args.host}:{args.port}")
    print("This version runs the browser in a separate process for improved stability")
    print("\nAPI Routes:")
    print("  GET  /status    - Get browser session status")
    print("  POST /start     - Start a new browser session")
    print("  POST /stop      - Stop the current browser session")
    print("  POST /execute   - Execute a natural language command")
    print("  POST /screenshot - Take a screenshot")
    print("  GET  /dom       - Get the current DOM snapshot")
    print("  POST /inspect   - Inspect a specific element")
    print("\nExample curl command:")
    print("  curl -X POST http://localhost:5020/execute -H \"Content-Type: application/json\" -d '{\"command\": \"Navigate to google.com\"}'")
    print("\nFor flight search:")
    print("  curl -X POST http://localhost:5020/execute -H \"Content-Type: application/json\" -d '{\"command\": \"Go to Google Flights, search for flights from LAX to SFO tomorrow, find the cheapest option, and tell me the price, departure time, and airline\"}'")
    
    # Start the Flask app
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main() 