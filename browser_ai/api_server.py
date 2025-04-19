#!/usr/bin/env python
"""
REST API server for Browser-AI to enable HTTP access (e.g., via curl)

Usage:
    python -m browser_ai.api_server

Example curl command:
    curl -X POST http://localhost:5020/execute -H "Content-Type: application/json" -d '{"command": "Navigate to google.com"}'
"""

import os
import sys
import json
import time
import argparse
import threading
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fix the import issue by using a relative import path or absolute path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    logger.info("Trying to import InteractAPI from browser_ai package...")
    from browser_ai.interact_api import InteractAPI
    logger.info("Successfully imported InteractAPI from package")
except ImportError as e:
    logger.warning(f"Import from package failed: {e}")
    try:
        # If that fails, try importing directly from the current directory
        logger.info("Trying to import InteractAPI from current directory...")
        from interact_api import InteractAPI
        logger.info("Successfully imported InteractAPI from current directory")
    except ImportError as e:
        logger.error(f"All imports failed: {e}")
        logger.error(f"Current Python path: {sys.path}")
        logger.error(f"Current directory: {os.getcwd()}")
        raise

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables for browser session management
browser_lock = threading.Lock()  # Lock for browser access
interact = None
browser_active = False
browser_last_error = None
browser_config = {
    "headless": False,
    "browser_type": "chromium"
}


def ensure_browser_is_active():
    """
    Check if browser is active and restart if necessary
    Returns a tuple of (is_active, error_message)
    """
    global interact, browser_active, browser_last_error, browser_config
    
    with browser_lock:
        # If browser is already active, just return
        if browser_active and interact and interact.is_session_active():
            return True, None
        
        # Try to restart the browser if it crashed or was never started
        try:
            logger.info("Attempting to (re)start browser session")
            
            # Clean up any existing session
            if interact:
                try:
                    interact.end_session()
                except Exception as e:
                    logger.warning(f"Error ending existing session: {e}")
            
            # Create new InteractAPI instance
            interact = InteractAPI(
                headless=browser_config["headless"], 
                browser_type=browser_config["browser_type"]
            )
            
            # Start browser session
            success = interact.start_session()
            if success:
                browser_active = True
                browser_last_error = None
                logger.info("Browser session (re)started successfully")
                return True, None
            else:
                browser_active = False
                error_msg = "Failed to start browser session"
                browser_last_error = error_msg
                logger.error(error_msg)
                return False, error_msg
        except Exception as e:
            browser_active = False
            error_msg = f"Error (re)starting browser: {str(e)}"
            browser_last_error = error_msg
            logger.error(error_msg)
            return False, error_msg


@app.route('/status', methods=['GET'])
def status():
    """Get the current status of the browser session"""
    global browser_active, interact, browser_last_error
    logger.info("Received request to /status endpoint")
    
    with browser_lock:
        if not browser_active or not interact:
            return jsonify({
                "status": "inactive",
                "message": "Browser session not started",
                "last_error": browser_last_error
            })
        
        try:
            # Check if browser is truly active
            if interact.is_session_active():
                # Get current page state
                page_state = interact.get_page_state()
                return jsonify({
                    "status": "active",
                    "page": page_state
                })
            else:
                browser_active = False
                return jsonify({
                    "status": "inactive",
                    "message": "Browser session disconnected",
                    "last_error": browser_last_error
                })
        except Exception as e:
            error_msg = f"Error checking browser status: {str(e)}"
            logger.error(error_msg)
            browser_active = False
            browser_last_error = error_msg
            return jsonify({
                "status": "error",
                "message": error_msg
            })


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
    
    # Start or restart the browser
    is_active, error = ensure_browser_is_active()
    
    if is_active:
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
    global browser_active, interact
    logger.info("Received request to /stop endpoint")
    
    with browser_lock:
        if not browser_active or not interact:
            return jsonify({
                "status": "inactive",
                "message": "No active browser session"
            })
        
        try:
            # End browser session
            success = interact.end_session()
            browser_active = False
            
            if success:
                logger.info("Browser session ended successfully")
                return jsonify({
                    "status": "success",
                    "message": "Browser session ended"
                })
            else:
                logger.error("Failed to end browser session properly")
                return jsonify({
                    "status": "warning",
                    "message": "Browser session closed with warnings"
                })
        except Exception as e:
            error_msg = f"Error ending browser session: {str(e)}"
            logger.error(error_msg)
            browser_active = False
            return jsonify({
                "status": "error",
                "message": error_msg
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
    
    # Make sure browser is active before executing command
    is_active, error = ensure_browser_is_active()
    if not is_active:
        return jsonify({
            "status": "error",
            "message": f"Could not ensure browser is active: {error}",
            "command": command
        })
    
    # Acquire lock for browser access
    with browser_lock:
        try:
            # Execute command
            max_attempts = 2  # Try twice in case of browser issues
            last_error = None
            
            for attempt in range(max_attempts):
                try:
                    result = interact.execute(command)
                    
                    # Enhance result with current page info
                    if not result.get('page_state'):
                        try:
                            result['page_state'] = interact.get_page_state()
                        except Exception as e:
                            logger.warning(f"Could not get page state after command: {e}")
                            result['page_state'] = {"warning": "Could not retrieve page state"}
                    
                    return jsonify({
                        "status": "success" if result.get('success', False) else "error",
                        "result": result
                    })
                except Exception as e:
                    last_error = str(e)
                    logger.error(f"Command execution failed (attempt {attempt+1}/{max_attempts}): {last_error}")
                    
                    # If this isn't the last attempt, try to restart the browser
                    if attempt < max_attempts - 1:
                        logger.info("Attempting to restart browser session before retrying")
                        # Try to restart browser
                        is_active, restart_error = ensure_browser_is_active()
                        if not is_active:
                            return jsonify({
                                "status": "error",
                                "message": f"Failed to restart browser: {restart_error}",
                                "command": command
                            })
                        # Wait a moment for browser to stabilize
                        time.sleep(1)
            
            # If we get here, all attempts failed
            return jsonify({
                "status": "error",
                "message": f"Command execution failed after {max_attempts} attempts: {last_error}",
                "command": command
            })
        except Exception as e:
            error_msg = f"Unexpected error executing command: {str(e)}"
            logger.error(error_msg)
            return jsonify({
                "status": "error",
                "message": error_msg,
                "command": command
            })


@app.route('/screenshot', methods=['POST'])
def take_screenshot():
    """Take a screenshot and return the file path"""
    logger.info("Received request to /screenshot endpoint")
    
    # Make sure browser is active
    is_active, error = ensure_browser_is_active()
    if not is_active:
        return jsonify({
            "status": "error",
            "message": f"Could not ensure browser is active: {error}"
        })
    
    # Get filename from request
    data = request.json or {}
    filename = data.get('filename', 'screenshot.png')
    
    with browser_lock:
        try:
            # Execute screenshot command
            result = interact.execute(f"Take a screenshot and save it as '{filename}'")
            
            return jsonify({
                "status": "success" if result.get('success', False) else "error",
                "filename": filename,
                "result": result
            })
        except Exception as e:
            error_msg = f"Screenshot failed: {str(e)}"
            logger.error(error_msg)
            return jsonify({
                "status": "error",
                "message": error_msg
            })


@app.route('/dom', methods=['GET'])
def get_dom():
    """Get the current DOM snapshot"""
    logger.info("Received request to /dom endpoint")
    
    # Make sure browser is active
    is_active, error = ensure_browser_is_active()
    if not is_active:
        return jsonify({
            "status": "error",
            "message": f"Could not ensure browser is active: {error}"
        })
    
    with browser_lock:
        try:
            # Get DOM snapshot
            snapshot = interact.get_dom_snapshot()
            
            return jsonify({
                "status": "success",
                "dom_snapshot": snapshot
            })
        except Exception as e:
            error_msg = f"DOM snapshot failed: {str(e)}"
            logger.error(error_msg)
            return jsonify({
                "status": "error",
                "message": error_msg
            })


@app.route('/inspect', methods=['POST'])
def inspect_element():
    """Inspect a specific element on the page"""
    logger.info("Received request to /inspect endpoint")
    
    # Make sure browser is active
    is_active, error = ensure_browser_is_active()
    if not is_active:
        return jsonify({
            "status": "error",
            "message": f"Could not ensure browser is active: {error}"
        })
    
    # Get selector from request
    data = request.json
    if not data or 'selector' not in data:
        return jsonify({
            "status": "error",
            "message": "Missing 'selector' in request body"
        })
    
    selector = data['selector']
    
    with browser_lock:
        try:
            # Inspect element
            element_info = interact.inspect_element(selector)
            
            if 'error' in element_info:
                return jsonify({
                    "status": "error",
                    "message": element_info['error']
                })
            
            return jsonify({
                "status": "success",
                "element": element_info
            })
        except Exception as e:
            error_msg = f"Element inspection failed: {str(e)}"
            logger.error(error_msg)
            return jsonify({
                "status": "error",
                "message": error_msg
            })


def main():
    """Main function to start the API server"""
    parser = argparse.ArgumentParser(description='Browser-AI REST API Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=5020, help='Port to bind the server to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not found in environment variables or .env file.")
        print("Please set your OpenAI API key before making API calls.")
    
    print(f"Starting Browser-AI API server at http://{args.host}:{args.port}")
    print("API Routes:")
    print("  GET  /status    - Get browser session status")
    print("  POST /start     - Start a new browser session")
    print("  POST /stop      - Stop the current browser session")
    print("  POST /execute   - Execute a natural language command")
    print("  POST /screenshot - Take a screenshot")
    print("  GET  /dom       - Get the current DOM snapshot")
    print("  POST /inspect   - Inspect a specific element")
    print("\nExample curl command:")
    print("  curl -X POST http://localhost:5020/execute -H \"Content-Type: application/json\" -d '{\"command\": \"Navigate to google.com\"}'")
    
    # Start the Flask app with threading enabled for concurrent requests
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == "__main__":
    main() 