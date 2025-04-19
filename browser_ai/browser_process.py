#!/usr/bin/env python
"""
Browser Process Module - Runs the browser in a separate process

This module provides a clean isolation between the Flask API server and
the Playwright browser automation processes to prevent thread conflicts.
"""

import os
import sys
import time
import json
import logging
import multiprocessing
from queue import Empty

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the InteractAPI
try:
    from browser_ai import InteractAPI
except ImportError:
    try:
        from browser_ai.interact_api import InteractAPI
    except ImportError:
        logger.error("Cannot import InteractAPI. Make sure the browser_ai package is in your Python path.")
        sys.exit(1)

class BrowserProcessManager:
    """
    Manages a separate process for the browser to avoid threading issues.
    Uses multiprocessing.Queue for communication between processes.
    """
    
    def __init__(self):
        """Initialize the browser process manager."""
        self.command_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.browser_process = None
        self.is_running = False
    
    def start(self, headless=False, browser_type="chromium"):
        """Start the browser process."""
        if self.is_running:
            logger.warning("Browser process is already running")
            return False, "Browser process is already running"
        
        # Create and start the browser process
        self.browser_process = multiprocessing.Process(
            target=self._browser_worker,
            args=(self.command_queue, self.result_queue, headless, browser_type)
        )
        self.browser_process.daemon = True  # Process will terminate when main process exits
        self.browser_process.start()
        self.is_running = True
        
        # Wait for browser startup confirmation
        try:
            result = self.result_queue.get(timeout=60)  # Wait up to 60 seconds for browser to start
            if result.get('success'):
                logger.info("Browser process started successfully")
                return True, None
            else:
                self.is_running = False
                error_msg = result.get('error', 'Unknown error starting browser')
                logger.error(f"Failed to start browser process: {error_msg}")
                return False, error_msg
        except Empty:
            self.is_running = False
            error_msg = "Timeout waiting for browser to start"
            logger.error(error_msg)
            return False, error_msg
    
    def stop(self):
        """Stop the browser process."""
        if not self.is_running:
            logger.warning("Browser process is not running")
            return True, None
        
        # Send stop command
        self.command_queue.put({"command_type": "stop"})
        
        # Wait for confirmation
        try:
            result = self.result_queue.get(timeout=30)
            success = result.get('success', False)
            error = result.get('error')
            
            # Terminate the process regardless of result
            if self.browser_process and self.browser_process.is_alive():
                self.browser_process.terminate()
                self.browser_process.join(timeout=5)
                
            self.is_running = False
            
            if success:
                logger.info("Browser process stopped successfully")
                return True, None
            else:
                logger.warning(f"Browser process stopped with warnings: {error}")
                return False, error
        except Empty:
            # Force terminate if no response
            if self.browser_process and self.browser_process.is_alive():
                self.browser_process.terminate()
                self.browser_process.join(timeout=5)
            
            self.is_running = False
            error_msg = "Timeout waiting for browser to stop"
            logger.error(error_msg)
            return False, error_msg
    
    def execute(self, command):
        """Execute a command in the browser process."""
        if not self.is_running:
            logger.error("Browser process is not running")
            return {"success": False, "error": "Browser process is not running"}
        
        # Send execute command
        self.command_queue.put({
            "command_type": "execute",
            "command": command
        })
        
        # Wait for result
        try:
            result = self.result_queue.get(timeout=300)  # Long timeout for complex operations
            return result
        except Empty:
            error_msg = "Timeout waiting for command execution"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def get_status(self):
        """Get the status of the browser process."""
        if not self.is_running:
            return {"status": "inactive", "message": "Browser process is not running"}
        
        # Send status command
        self.command_queue.put({"command_type": "status"})
        
        # Wait for result
        try:
            result = self.result_queue.get(timeout=10)
            return result
        except Empty:
            self.is_running = False
            error_msg = "Timeout waiting for status response"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    def take_screenshot(self, filename="screenshot.png"):
        """Take a screenshot."""
        return self.execute(f"Take a screenshot and save it as '{filename}'")
    
    def get_dom_snapshot(self):
        """Get the DOM snapshot."""
        if not self.is_running:
            logger.error("Browser process is not running")
            return {"success": False, "error": "Browser process is not running"}
        
        # Send DOM snapshot command
        self.command_queue.put({"command_type": "dom_snapshot"})
        
        # Wait for result
        try:
            result = self.result_queue.get(timeout=30)
            return result
        except Empty:
            error_msg = "Timeout waiting for DOM snapshot"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def inspect_element(self, selector):
        """Inspect an element."""
        if not self.is_running:
            logger.error("Browser process is not running")
            return {"success": False, "error": "Browser process is not running"}
        
        # Send inspect element command
        self.command_queue.put({
            "command_type": "inspect_element",
            "selector": selector
        })
        
        # Wait for result
        try:
            result = self.result_queue.get(timeout=10)
            return result
        except Empty:
            error_msg = "Timeout waiting for element inspection"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    @staticmethod
    def _browser_worker(command_queue, result_queue, headless, browser_type):
        """
        Worker function to run in a separate process.
        Handles all browser interactions.
        """
        interact = None
        
        try:
            # Initialize the browser
            logger.info(f"Initializing browser (headless={headless}, type={browser_type})")
            interact = InteractAPI(headless=headless, browser_type=browser_type)
            
            # Start browser session
            if not interact.start_session():
                result_queue.put({"success": False, "error": "Failed to start browser session"})
                return
            
            # Notify successful startup
            result_queue.put({"success": True})
            logger.info("Browser session started successfully")
            
            # Main command processing loop
            while True:
                try:
                    # Get next command (blocking)
                    command_data = command_queue.get(block=True)
                    command_type = command_data.get("command_type")
                    
                    logger.info(f"Processing command: {command_type}")
                    
                    # Process the command
                    if command_type == "stop":
                        # Stop the browser
                        try:
                            interact.end_session()
                            result_queue.put({"success": True})
                        except Exception as e:
                            result_queue.put({"success": False, "error": str(e)})
                        break
                    
                    elif command_type == "execute":
                        # Execute a command
                        try:
                            command = command_data.get("command")
                            result = interact.execute(command)
                            result_queue.put(result)
                        except Exception as e:
                            result_queue.put({"success": False, "error": str(e)})
                    
                    elif command_type == "status":
                        # Get browser status
                        try:
                            if interact.is_session_active():
                                page_state = interact.get_page_state()
                                result_queue.put({"status": "active", "page": page_state})
                            else:
                                result_queue.put({"status": "inactive", "message": "Browser session is not active"})
                        except Exception as e:
                            result_queue.put({"status": "error", "message": str(e)})
                    
                    elif command_type == "dom_snapshot":
                        # Get DOM snapshot
                        try:
                            snapshot = interact.get_dom_snapshot()
                            result_queue.put({"success": True, "dom_snapshot": snapshot})
                        except Exception as e:
                            result_queue.put({"success": False, "error": str(e)})
                    
                    elif command_type == "inspect_element":
                        # Inspect element
                        try:
                            selector = command_data.get("selector")
                            element_info = interact.inspect_element(selector)
                            result_queue.put({"success": True, "element": element_info})
                        except Exception as e:
                            result_queue.put({"success": False, "error": str(e)})
                    
                    else:
                        # Unknown command
                        result_queue.put({"success": False, "error": f"Unknown command type: {command_type}"})
                
                except Exception as e:
                    logger.error(f"Error processing command: {str(e)}")
                    try:
                        result_queue.put({"success": False, "error": f"Error processing command: {str(e)}"})
                    except:
                        pass
        
        except Exception as e:
            logger.error(f"Browser worker initialization error: {str(e)}")
            try:
                result_queue.put({"success": False, "error": str(e)})
            except:
                pass
        
        finally:
            # Ensure browser is closed
            try:
                if interact:
                    interact.end_session()
            except:
                pass

# Simple test if run directly
if __name__ == "__main__":
    print("Testing browser process manager...")
    manager = BrowserProcessManager()
    
    print("\nStarting browser process...")
    success, error = manager.start(headless=False)
    
    if success:
        print("Browser process started successfully")
        
        print("\nNavigating to Google...")
        result = manager.execute("Navigate to google.com")
        print(f"Success: {result.get('success', False)}")
        
        print("\nGetting status...")
        status = manager.get_status()
        print(f"Status: {status.get('status')}")
        
        print("\nTaking screenshot...")
        screenshot = manager.take_screenshot("test_process.png")
        print(f"Screenshot success: {screenshot.get('success', False)}")
        
        print("\nStopping browser process...")
        success, error = manager.stop()
        print(f"Stop success: {success}")
        if error:
            print(f"Stop error: {error}")
    else:
        print(f"Failed to start browser process: {error}") 