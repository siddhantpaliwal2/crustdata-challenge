import os
import json
import logging
import time
from typing import Dict, Any, List, Optional, Union, Tuple
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from browser_ai.utils.nlp_engine import NLPEngine
from browser_ai.utils.browser_actions import BrowserActions

# set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InteractAPI:
    """
    main api for interacting with a browser using natural language commands
    """
    
    def __init__(self, headless: bool = False, browser_type: str = "chromium"):
        """
        initialize the interact api
        
        args:
            headless: whether to run the browser in headless mode
            browser_type: which browser to use (chromium, firefox, or webkit)
        """
        self.headless = headless
        self.browser_type = browser_type
        self.nlp_engine = NLPEngine()
        
        # playwright objects - will be initialized when session starts
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        # action history for tracking what has been done
        self.action_history = []
        
        # dom snapshot cache
        self.current_dom_snapshot = None
        self.dom_snapshot_timestamp = 0
        
        # action mapping to browser functions
        self.action_map = {
            "navigate": BrowserActions.navigate,
            "click": BrowserActions.click,
            "fill": BrowserActions.fill,
            "wait": BrowserActions.wait,
            "scroll": BrowserActions.scroll,
            "back": BrowserActions.back,
            "forward": BrowserActions.forward,
            "reload": BrowserActions.reload,
            "screenshot": BrowserActions.screenshot,
            "select": BrowserActions.select,
            "dom_snapshot": BrowserActions.dom_snapshot
        }
    
    def start_session(self, user_data_dir: Optional[str] = None) -> bool:
        """
        start a new browser session
        
        args:
            user_data_dir: path to user data directory (for persistent sessions)
            
        returns:
            whether the session was successfully started
        """
        try:
            # initialize playwright
            self.playwright = sync_playwright().start()
            
            # select the appropriate browser
            if self.browser_type == "chromium":
                browser_instance = self.playwright.chromium
            elif self.browser_type == "firefox":
                browser_instance = self.playwright.firefox
            elif self.browser_type == "webkit":
                browser_instance = self.playwright.webkit
            else:
                raise ValueError(f"Unknown browser type: {self.browser_type}")
            
            # launch browser
            launch_args = {"headless": self.headless}
            if user_data_dir:
                launch_args["user_data_dir"] = user_data_dir
                
            self.browser = browser_instance.launch(**launch_args)
            
            # create context
            self.context = self.browser.new_context(
                viewport={"width": 1280, "height": 800}
            )
            
            # create page
            self.page = self.context.new_page()
            
            # set default timeout
            self.page.set_default_timeout(30000)  # 30 seconds
            
            logger.info(f"Browser session started (type: {self.browser_type}, headless: {self.headless})")
            return True
        except Exception as e:
            logger.error(f"Failed to start browser session: {str(e)}")
            self.end_session()  # clean up any partially initialized resources
            return False
    
    def end_session(self) -> bool:
        """
        end the current browser session
        
        returns:
            whether the session was successfully ended
        """
        try:
            # close resources in reverse order of creation
            if self.page:
                self.page.close()
                self.page = None
                
            if self.context:
                self.context.close()
                self.context = None
                
            if self.browser:
                self.browser.close()
                self.browser = None
                
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
                
            logger.info("Browser session ended")
            return True
        except Exception as e:
            logger.error(f"Error ending browser session: {str(e)}")
            return False
    
    def execute(self, command: str) -> Dict[str, Any]:
        """
        execute a natural language command
        
        args:
            command: the natural language command to execute
            
        returns:
            dictionary with results of execution
        """
        # check if session is active
        if not self.is_session_active():
            error_msg = "No active browser session. Call start_session() first."
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
        try:
            # get current page state for context
            page_state = BrowserActions.get_page_state(self.page)
            
            # get dom snapshot for better context (with caching to avoid too frequent snapshots)
            current_time = time.time()
            if self.current_dom_snapshot is None or (current_time - self.dom_snapshot_timestamp) > 2:
                success, dom_snapshot = BrowserActions.dom_snapshot(self.page, {})
                if success:
                    self.current_dom_snapshot = dom_snapshot
                    self.dom_snapshot_timestamp = current_time
            
            # create enhanced context with dom snapshot
            enhanced_context = {
                "page_state": page_state,
                "dom_snapshot": self.current_dom_snapshot
            }
            
            # parse command into actionable steps with enhanced context
            action_data = self.nlp_engine.parse_command(command, enhanced_context)
            
            # handle multi-step actions (a sequence of actions)
            if "actions" in action_data and isinstance(action_data["actions"], list):
                return self._execute_multi_step_actions(action_data["actions"], command)
            
            # handle single action
            return self._execute_single_action(action_data, command)
            
        except Exception as e:
            error_msg = f"Command execution failed: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "command": command
            }
    
    def _execute_single_action(self, action_data: Dict[str, Any], command: str) -> Dict[str, Any]:
        """
        execute a single action
        
        args:
            action_data: the action data from nlp engine
            command: the original command (for reference)
            
        returns:
            dictionary with results of execution
        """
        # check for error from NLP engine
        if action_data.get("action_type") == "error":
            return {
                "success": False,
                "error": action_data.get("error", "Unknown error"),
                "command": command
            }
            
        action_type = action_data.get("action_type", "").lower()
        
        # check if action type is supported
        if action_type not in self.action_map:
            error_msg = f"Unsupported action type: {action_type}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "command": command
            }
            
        # execute the action
        logger.info(f"Executing action: {action_type}")
        success, error = self.action_map[action_type](self.page, action_data)
        
        # record action in history
        self.action_history.append({
            "command": command,
            "action": action_data,
            "success": success,
            "error": error
        })
        
        # if action failed, try fallback strategies
        if not success and error:
            logger.warning(f"Action failed: {error}")
            return self._try_fallback_strategies(action_data, command, error)
        
        # action succeeded
        page_state = BrowserActions.get_page_state(self.page)
        return {
            "success": True,
            "action": action_type,
            "command": command,
            "page_state": page_state
        }
    
    def _execute_multi_step_actions(self, actions: List[Dict[str, Any]], command: str) -> Dict[str, Any]:
        """
        execute a sequence of actions
        
        args:
            actions: list of actions to execute
            command: the original command (for reference)
            
        returns:
            dictionary with results of execution
        """
        results = []
        overall_success = True
        
        for i, action in enumerate(actions):
            logger.info(f"Executing step {i+1} of {len(actions)}")
            result = self._execute_single_action(action, f"{command} (step {i+1})")
            results.append(result)
            
            # if any action fails, stop execution
            if not result.get("success", False):
                overall_success = False
                break
                
        # get final page state
        page_state = BrowserActions.get_page_state(self.page)
        
        return {
            "success": overall_success,
            "results": results,
            "command": command,
            "page_state": page_state
        }
    
    def _try_fallback_strategies(self, action_data: Dict[str, Any], command: str, error: str) -> Dict[str, Any]:
        """
        try fallback strategies when an action fails
        
        args:
            action_data: the failed action data
            command: the original command
            error: the error message
            
        returns:
            dictionary with results of execution
        """
        # check if action already has fallback strategies
        fallbacks = action_data.get("fallback_strategies", [])
        
        # if no fallbacks defined, ask nlp engine for suggestions
        if not fallbacks:
            fallbacks = self.nlp_engine.generate_fallback_strategies(action_data, error)
        
        # try each fallback strategy
        for i, fallback in enumerate(fallbacks):
            logger.info(f"Trying fallback strategy {i+1} of {len(fallbacks)}")
            
            # execute the fallback action
            action_type = fallback.get("action_type", "").lower()
            if action_type in self.action_map:
                success, fallback_error = self.action_map[action_type](self.page, fallback)
                
                # record fallback in history
                self.action_history.append({
                    "command": f"{command} (fallback {i+1})",
                    "action": fallback,
                    "success": success,
                    "error": fallback_error
                })
                
                # if fallback succeeded, return success
                if success:
                    page_state = BrowserActions.get_page_state(self.page)
                    return {
                        "success": True,
                        "action": action_type,
                        "command": command,
                        "used_fallback": True,
                        "fallback_index": i,
                        "page_state": page_state
                    }
        
        # all fallbacks failed
        return {
            "success": False,
            "error": f"All strategies failed. Original error: {error}",
            "command": command,
            "tried_fallbacks": len(fallbacks)
        }
    
    def is_session_active(self) -> bool:
        """
        check if a browser session is active
        
        returns:
            whether a session is active
        """
        return self.page is not None and self.browser is not None
    
    def get_page_state(self) -> Dict[str, Any]:
        """
        get the current state of the page
        
        returns:
            dictionary with page state information
        """
        if not self.is_session_active():
            return {"error": "No active browser session"}
            
        return BrowserActions.get_page_state(self.page)
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        get the history of executed actions
        
        returns:
            list of action history entries
        """
        return self.action_history
    
    def save_history(self, filepath: str) -> bool:
        """
        save action history to a file
        
        args:
            filepath: path to save the history
            
        returns:
            whether the save was successful
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.action_history, f, indent=2)
            logger.info(f"Action history saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save action history: {str(e)}")
            return False
    
    def get_dom_snapshot(self) -> Dict[str, Any]:
        """
        get a snapshot of the current page dom
        
        returns:
            dictionary with dom snapshot data
        """
        if not self.is_session_active():
            return {"error": "No active browser session"}
        
        success, snapshot = BrowserActions.dom_snapshot(self.page, {})
        if success:
            self.current_dom_snapshot = snapshot
            self.dom_snapshot_timestamp = time.time()
            return snapshot
        else:
            return {"error": "Failed to get DOM snapshot"}
    
    def inspect_element(self, selector: str) -> Dict[str, Any]:
        """
        inspect a specific element on the page
        
        args:
            selector: css selector for the element
            
        returns:
            dictionary with element details
        """
        if not self.is_session_active():
            return {"error": "No active browser session"}
            
        try:
            # check if element exists
            if not self.page.is_visible(selector):
                return {"error": f"Element with selector '{selector}' is not visible"}
                
            # get element properties
            element_info = self.page.evaluate("""(selector) => {
                const el = document.querySelector(selector);
                if (!el) return null;
                
                return {
                    tagName: el.tagName.toLowerCase(),
                    id: el.id || '',
                    className: el.className || '',
                    innerText: (el.innerText || '').substring(0, 200),
                    textContent: (el.textContent || '').substring(0, 200),
                    href: el.href || '',
                    src: el.src || '',
                    type: el.type || '',
                    value: el.value || '',
                    placeholder: el.placeholder || '',
                    attributes: Array.from(el.attributes).map(attr => ({
                        name: attr.name,
                        value: attr.value
                    })),
                    rect: {
                        x: el.getBoundingClientRect().x,
                        y: el.getBoundingClientRect().y,
                        width: el.getBoundingClientRect().width,
                        height: el.getBoundingClientRect().height
                    },
                    isVisible: (
                        el.offsetWidth > 0 && 
                        el.offsetHeight > 0 &&
                        window.getComputedStyle(el).visibility !== 'hidden' &&
                        window.getComputedStyle(el).display !== 'none'
                    )
                };
            }""", selector)
            
            if not element_info:
                return {"error": f"Element with selector '{selector}' not found"}
                
            return element_info
        except Exception as e:
            error_msg = f"Element inspection failed: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg} 